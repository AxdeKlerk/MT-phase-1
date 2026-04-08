console.log("Script Loaded");

document.addEventListener("DOMContentLoaded", () => {
    const tipSection = document.getElementById("tip-section");
    if (!tipSection) return;

    let selectedAmount = null;
    let walletButtonMounted = false;
    
    const artistName = tipSection.dataset.artistName;
    const startUrl = tipSection.dataset.startUrl;
    const csrfToken = tipSection.dataset.csrf;

    const amountButtons = document.querySelectorAll(".tip-btn");
    const confirmationText = document.getElementById("tip-confirmation");
    const payButton = document.getElementById("pay-btn");
    const payConfirmation = document.getElementById("pay-confirmation");

    // Initialise Stripe
    const stripe = Stripe(window.STRIPE_PUBLIC_KEY);
    const elements = stripe.elements();
    const style = {
        base: {
            color: "#000000",
            fontFamily: "Geist Mono, monospace",
            fontSize: "16px",
            "::placeholder": {
            color: "#555555"
            }
        },
        invalid: {
            color: "#E63946"
        }
    };

    // Create paymentRequest using selected amount
    let paymentRequest = stripe.paymentRequest({
        country: "GB",
        currency: "gbp",
        total: {
            label: `Tip`,
            amount: 0, // Will be updated when amount is selected   
        },
        requestPayerName: true,
        requestPayerEmail: true,
    });

    const cardNumber = elements.create("cardNumber", { style: style });
    const cardExpiry = elements.create("cardExpiry", { style: style });
    const cardCvc = elements.create("cardCvc", { style: style });

    cardNumber.mount("#card-number");
    cardExpiry.mount("#card-expiry");
    cardCvc.mount("#card-cvc");

    const urlParams = new URLSearchParams(window.location.search);
    const paymentSuccess = urlParams.get("payment");

    if (paymentSuccess === "success") {
        document.getElementById("payment-ui").classList.add("d-none");

        const confirmationText = document.getElementById("tip-confirmation");
        confirmationText.textContent = "Thank you for supporting live music!";
        confirmationText.classList.remove("d-none");
    }    

    // Amount selection
    amountButtons.forEach(button => {
        button.addEventListener("click", async () => {
            let data;

            selectedAmount = button.dataset.amount;

            if (button.classList.contains("active")) {
                return;
            }

            try {
                const response = await fetch(startUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": csrfToken
                    },
                    body: JSON.stringify({
                        gig_id: tipSection.dataset.gigId,
                        amount: parseFloat(selectedAmount)
                    })
                });

                data = await response.json();

                // Update Pay button UI
                payButton.textContent = `Pay £${data.total_amount} Now`;
                payButton.dataset.totalAmount = data.total_amount;
                payButton.dataset.clientSecret = data.client_secret;

            } catch (error) {
                console.error("Payment init failed:", error);

                payButton.disabled = true;
                payButton.textContent = "Error — try again";

                return;
            }

        const feeMessage = document.getElementById("fee-message");

        if (data.cover_processing_fees) {
            feeMessage.textContent = "Processing fees included for day 1";
        } else {
            feeMessage.textContent = "Processing fee: 1.4% + 20p added at checkout";
        }

        feeMessage.classList.remove("d-none");

        button.dataset.clientSecret = data.client_secret;
        payButton.dataset.clientSecret = data.client_secret;

        const totalAmount = Math.round(parseFloat(data.total_amount) * 100);
        paymentRequest.update({
            total: {
                label: `Tip £${selectedAmount}`,
                amount: totalAmount,
            }
        });

        // ===== Wallet Setup =====
        const walletContainer = document.getElementById("wallet-button-container");

        let prButton;

        if (!walletButtonMounted) {
            prButton = elements.create("paymentRequestButton", {
                paymentRequest,
            });
            walletButtonMounted = true;
        }

        // Check if wallet is supported
        paymentRequest.canMakePayment().then((result) => {
            
            document.getElementById("tip-confirmation").textContent = "WALLET EVENT TRIGGERED";
            document.getElementById("tip-confirmation").classList.remove("d-none");

            console.log("Wallet support result:", result);
            
            if (result) {
                walletContainer.classList.remove("d-none");
                if (prButton) {
                    prButton.mount("#wallet-button-container");
                }
            } else {
                walletContainer.classList.add("d-none");
            }
        });        

        paymentRequest.on("paymentmethod", async (ev) => {
            const clientSecret = payButton.dataset.clientSecret;

            if (!clientSecret) {
                ev.complete("fail");
                return;
            }

        const { error, paymentIntent } = await stripe.confirmCardPayment(
            clientSecret,
            { payment_method: ev.paymentMethod.id },
            { handleActions: false }
        );

        console.log("WALLET STATUS:", paymentIntent.status);

        if (error) {
            ev.complete("fail");
            document.getElementById("card-errors").textContent = error.message;
            } 
        
        else {
            ev.complete("success");
            payButton.disabled = true;
            payButton.textContent = "Select an Amount to Tip";
            amountButtons.forEach(btn => {
                btn.disabled = false;
                btn.classList.remove("active");
            });
        }
        }); 

            amountButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            payButton.disabled = false;
            payButton.textContent = `Confirm and Tip £${selectedAmount}`;
        
        });
    });

    // Pay button
    payButton.addEventListener("click", async () => {
        if (!selectedAmount) return;

        // If client secret already exists → confirm payment
        if (payButton.dataset.clientSecret) {

            document.getElementById("card-container").classList.remove("d-none");

            payButton.disabled = true;
            payButton.textContent = "Processing...";

            const { error, paymentIntent } = await stripe.confirmCardPayment(
                payButton.dataset.clientSecret,
                {
                    payment_method: {
                        card: cardNumber
                    }
                }
            );

            if (error) {
                document.getElementById("card-errors").textContent = error.message;
                payButton.disabled = false;
                payButton.textContent = `Pay £${payButton.dataset.totalAmount} Now`;
                
            } else if (paymentIntent.status === "succeeded") {

                console.log("SUCCESS BLOCK HIT");

                payButton.textContent = "Tip Completed";

                document.getElementById("payment-ui").classList.add("d-none");

                const backLink = document.getElementById("back-link");
                backLink.classList.add("mt-3");
                document.getElementById("tip-confirmation").after(backLink);
                
                // Hide card container
                document.getElementById("card-container").classList.add("d-none");

                // Show thank you messages
                confirmationText.innerHTML = `You are an absolute legend!<br>
                <span class="fs-6 fst-italic">Thank you for supporting live music!</span>
                <span class="fs-1 fw-bold mt-0" style="color: red;">${artistName}</span>`;
                   
                confirmationText.classList.remove("d-none");
                
                // Reset selection state
                selectedAmount = null;

                // Reset pay button
                payButton.disabled = true;
                payButton.textContent = "Select an Amount to Tip";
                delete payButton.dataset.clientSecret;

                // Disable amount buttons
                amountButtons.forEach(btn => {
                    btn.disabled = true;
                    btn.classList.remove("active")
                    btn.classList.add("opacity-50"); // optional visual grey-out
                });

                return;
            }
        }
    });
});

