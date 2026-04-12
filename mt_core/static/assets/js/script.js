console.log("Script Loaded");

document.addEventListener("DOMContentLoaded", () => {
    const tipSection = document.getElementById("tip-section");
    if (!tipSection) return;

    let selectedAmount = null;
    let walletButtonMounted = false;
    let walletButtonIsMounted = false;
    let prButton = null;
    let paymentComplete = false;

    const artistName = tipSection.dataset.artistName;
    const startUrl = tipSection.dataset.startUrl;
    const csrfToken = tipSection.dataset.csrf;

    const amountButtons = document.querySelectorAll(".tip-btn");
    const confirmationText = document.getElementById("tip-confirmation");
    const payButton = document.getElementById("pay-btn");
    const backLink = document.getElementById("back-link");

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

    // Shared post-payment lockdown — called by both card and wallet flows once a payment has succeeded
    function lockdownAfterPayment() {
        paymentComplete = true;

        // Freeze all amount buttons in place & disable them, to prevent confusion and multiple payments
        amountButtons.forEach(btn => {
            btn.disabled = true;
            btn.classList.remove("active");
            btn.style.pointerEvents = "none";
            btn.style.opacity = "0.5";
            btn.blur();
        });

        // Hide the plain link
        if (backLink) {
            backLink.classList.add("d-none");
        }

        // Move the CTA below the confirmation message
        const backCta = document.getElementById("back-cta");
        if (backCta && !backCta.dataset.moved) {
            confirmationText.after(backCta);
            backCta.classList.remove("d-none");
            backCta.dataset.moved = "true";
        }
    }

    // Card and wallet flows shared confirmation display
    function showConfirmation() {
        document.getElementById("payment-ui").classList.add("d-none");

        confirmationText.innerHTML = `
            <div class="mb-0" style="line-height: 0.5; color: red;">You are an absolute legend</div>
            <div class="fs-6 fst-italic mt-0 mb-" style="line-height: 0.5;">Thank you for supporting live music</div>`;

        confirmationText.classList.remove("d-none");
    }

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

        if (error) {
            ev.complete("fail");
            document.getElementById("card-errors").textContent = error.message;
            return;
        }

        ev.complete("success");

        if (paymentIntent.status === "succeeded") {
            console.log("WALLET SUCCESS BLOCK HIT");
            showConfirmation();
            lockdownAfterPayment();
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
                    label: `Tip £${selectedAmount}`,
                    amount: totalAmount,
                }
            });

            // Wallet button — create once, mount once
            const walletContainer = document.getElementById("wallet-button-container");

            if (!walletButtonMounted) {
                prButton = elements.create("paymentRequestButton", { paymentRequest });
                walletButtonMounted = true;
            }

            paymentRequest.canMakePayment().then((result) => {
                if (result) {
                    walletContainer.classList.remove("d-none");
                    if (prButton && !walletButtonIsMounted) {
                        prButton.mount("#wallet-button-container");
                        walletButtonIsMounted = true;
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
        if (!selectedAmount || !payButton.dataset.clientSecret) return;

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
            payButton.textContent = `Tip £${selectedAmount} Now`;

        } else if (paymentIntent.status === "succeeded") {
            console.log("CARD SUCCESS BLOCK HIT");
            showConfirmation();
            lockdownAfterPayment();
        }
    });
});