console.log("Script Loaded");

document.addEventListener("DOMContentLoaded", () => {
    const tipSection = document.getElementById("tip-section");
    if (!tipSection) return;

    let selectedAmount = null;
    let walletButtonMounted = false;
    let prButton = null;
    let paymentComplete = false;

    const artistName = tipSection.dataset.artistName;
    const startUrl = tipSection.dataset.startUrl;
    const csrfToken = tipSection.dataset.csrf;

    const amountButtons = document.querySelectorAll(".tip-btn");
    const confirmationText = document.getElementById("tip-confirmation");
    const payButton = document.getElementById("pay-btn");

    // Initialise Stripe
    const stripeInstance = Stripe(window.STRIPE_PUBLIC_KEY);
    const elements = stripeInstance.elements();

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

    // Create paymentRequest FIRST
    let paymentRequest = stripeInstance.paymentRequest({
        country: "GB",
        currency: "gbp",
        total: {
            label: "Tip",
            amount: 0,
        },
        requestPayerName: true,
        requestPayerEmail: true,
    });

    // Register wallet handler ONCE
    paymentRequest.on("paymentmethod", async (ev) => {
        const clientSecret = payButton.dataset.clientSecret;

        if (!clientSecret) {
            ev.complete("fail");
            return;
        }

        const { error, paymentIntent } = await stripeInstance.confirmCardPayment(
            clientSecret,
            { payment_method: ev.paymentMethod.id },
        );

        console.log("WALLET STATUS:", paymentIntent.status);

        if (error) {
            ev.complete("fail");
            document.getElementById("card-errors").textContent = error.message;
        } else {
            ev.complete("success");

            if (paymentIntent.status === "succeeded") {

                console.log("WALLET SUCCESS BLOCK HIT");

                document.getElementById("payment-ui").classList.add("d-none");

                confirmationText.innerHTML = `You are an absolute legend!<br>
                <span class="fs-6 fst-italic">Thank you for supporting live music!</span>
                <span class="fs-1 fw-bold mt-0" style="color: red;">${artistName}</span>`;

                confirmationText.classList.remove("d-none");
                paymentComplete = true;
            }

            payButton.disabled = true;
            payButton.textContent = "Select an Amount to Tip";

            amountButtons.forEach(btn => {
                btn.disabled = true;
                btn.classList.remove("active");
                btn.blur();
                btn.style.pointerEvents = "none";
                btn.style.opacity = "0.5";
            });
        }
    });

    // Card Elements
    const cardNumber = elements.create("cardNumber", { style });
    const cardExpiry = elements.create("cardExpiry", { style });
    const cardCvc = elements.create("cardCvc", { style });

    cardNumber.mount("#card-number");
    cardExpiry.mount("#card-expiry");
    cardCvc.mount("#card-cvc");

    // Amount selection
    amountButtons.forEach(button => {
        button.addEventListener("click", async () => {
            if (paymentComplete || button.disabled) return;
            let data;
            selectedAmount = button.dataset.amount;

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

                payButton.dataset.totalAmount = data.total_amount;
                payButton.dataset.clientSecret = data.client_secret;
                payButton.textContent = `Pay £${payButton.dataset.totalAmount} Now`;

                document.getElementById("card-container").classList.remove("d-none");

            } catch (error) {
                console.error("Payment init failed:", error);
                payButton.disabled = true;
                payButton.textContent = "Error — try again";
                return;
            }

            const totalAmount = Math.round(parseFloat(data.total_amount) * 100);

            paymentRequest.update({
                total: {
                    label: `Tip £${selectedAmount} Now`,
                    amount: totalAmount,
                }
            });

            // Wallet button
            const walletContainer = document.getElementById("wallet-button-container");

            if (!walletButtonMounted) {
                prButton = elements.create("paymentRequestButton", {
                    paymentRequest,
                });
                walletButtonMounted = true;
            }

            paymentRequest.canMakePayment().then((result) => {
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

            amountButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            payButton.disabled = false;
            payButton.textContent = `Tip £${selectedAmount} Now`;
        });
    });

    // Card payment flow 
    payButton.addEventListener("click", async () => {
        if (!selectedAmount) return;

        if (payButton.dataset.clientSecret) {
            payButton.disabled = true;
            payButton.textContent = "Processing...";

            const { error, paymentIntent } = await stripeInstance.confirmCardPayment(
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

                document.getElementById("payment-ui").classList.add("d-none");

                confirmationText.innerHTML = `You are an absolute legend!<br>
                <span class="fs-6 fst-italic">Thank you for supporting live music!</span>
                <span class="fs-1 fw-bold mt-0" style="color: red;">${artistName}</span>`;

                confirmationText.classList.remove("d-none");
                paymentComplete = true;

                amountButtons.forEach(btn => {
                    btn.disabled = true;
                    btn.classList.remove("active");
                    btn.blur();
                    btn.style.pointerEvents = "none";
                    btn.style.opacity = "0.5";
                });
                
            }
        }
    });
});