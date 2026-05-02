document.addEventListener("DOMContentLoaded", () => {
    const tipSection = document.getElementById("tip-section");
    if (!tipSection) return;

    let selectedAmount = null;
    let currentClientSecret = null;
    let walletButtonInitialised = false;  // Single flag — replaces walletButtonMounted + walletButtonIsMounted
    let prButton = null;
    let paymentComplete = false;
    let fetchInFlight = false; // Prevents duplicate fetches from rapid/double clicks

    const startUrl = tipSection.dataset.startUrl;
    const csrfToken = tipSection.dataset.csrf;

    const amountButtons = document.querySelectorAll(".tip-btn");
    const confirmationText = document.getElementById("tip-confirmation");
    const payButton = document.getElementById("pay-btn");
    const backLink = document.getElementById("back-link");
    const feeMessage = document.getElementById("fee-message");

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
            btn.blur();
            btn.disabled = true;
            btn.classList.remove("active");
            btn.style.pointerEvents = "none";
            btn.style.opacity = "0.5";
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

    // Check wallet availability once on page load — must run before any user gesture
    let walletAvailable = false;

    paymentRequest.canMakePayment().then((result) => {
        walletAvailable = !!result;
    });

    // Register wallet handler ONCE
    paymentRequest.on("paymentmethod", async (ev) => {
        const clientSecret = currentClientSecret;

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
            if (paymentComplete || button.disabled || fetchInFlight || currentClientSecret) return;

            fetchInFlight = true;

            let data;
            selectedAmount = button.dataset.amount;

            // Disable buttons and show loading state while fetching
            amountButtons.forEach(btn => {
                btn.disabled = true;

                if (btn === button) {
                    btn.classList.add("active");
                } else {
                    btn.classList.remove("active");
                    btn.style.opacity = "0.5";
                }
            });

            payButton.disabled = true;
            payButton.textContent = "Loading...";

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

                currentClientSecret = data.client_secret;
                payButton.dataset.clientSecret = data.client_secret;

                document.getElementById("card-container").classList.remove("d-none");

            } catch (error) {

                // Re-enable buttons so user can retry
                amountButtons.forEach(btn => {
                    btn.disabled = false;
                    btn.style.opacity = "1";
                    btn.classList.remove("active");
                });

                button.classList.remove("active");
                selectedAmount = null;
                payButton.disabled = true;
                payButton.textContent = "Select an Amount to Tip";
                document.getElementById("card-errors").textContent = "Something went wrong — please try again.";

                // IMPORTANT: release lock on error
                setTimeout(() => {
                    fetchInFlight = false;
                }, 0);

                return;
            }

            const totalAmount = Math.round(parseFloat(data.total_amount) * 100);
            const feeAmount = parseFloat(data.fee_amount || 0);
            const coversFees = data.cover_processing_fees;

            // Show fee message for day 1 and day 2
            if (coversFees) {
                feeMessage.innerHTML = `Processing fees are covered by MOSHTIP<br>
                    for DAY 1 of this pilot!`;
                feeMessage.classList.remove("d-none");
            } else if (feeAmount > 0) {
                // feeMessage.textContent = `Processing fees are NOT covered for DAY 2 of this pilot.<br>Stripe's payment processor fee of £${feeAmount.toFixed(2)} is added at checkout.`;
                feeMessage.innerHTML = `Processing fees are <span style="color:#E63946; fs-3 fw-bold">NOT</span> covered by MOSHTIP<br>
                    for DAY 2 of this pilot.<br>
                    Stripe's payment processor fee of <span style="color:#E63946; fs-3 fw-bold">£${feeAmount.toFixed(2)}</span><br>
                    will be added at checkout.`;
                feeMessage.classList.remove("d-none");
            } else {
                feeMessage.classList.add("d-none");
            }
            paymentRequest.update({
                total: {
                    label: `Tip £${selectedAmount}`,
                    amount: totalAmount,
                }
            });

            // Wallet button — create and mount once only, using pre-fetched availability
            const walletContainer = document.getElementById("wallet-button-container");

            if (!walletButtonInitialised && walletAvailable) {
                prButton = elements.create("paymentRequestButton", { paymentRequest });
                walletButtonInitialised = true;
                walletContainer.classList.remove("d-none");
                prButton.mount("#wallet-button-container");
            } else if (!walletAvailable) {
                walletContainer.classList.add("d-none");
            }

            // Update pay button with real charge amount (fee-inclusive)
            payButton.disabled = false;
            payButton.textContent = `Pay £${parseFloat(data.total_amount).toFixed(2)} Now`;

            // Release fetch lock after everything is fully set up
            setTimeout(() => {
                fetchInFlight = false;
            }, 0);
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
            // Guard against NaN if totalAmount dataset was never populated
            const displayAmount = payButton.dataset.totalAmount
                ? `Pay £${parseFloat(payButton.dataset.totalAmount).toFixed(2)} Now`
                : "Select an Amount to Tip";
            payButton.textContent = displayAmount;

        } else if (paymentIntent.status === "succeeded") {
            showConfirmation();
            lockdownAfterPayment();
        }
    });
});