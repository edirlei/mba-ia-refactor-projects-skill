class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
    }

    checkout(command) {
        return this.checkoutService.checkout(command);
    }
}

module.exports = { CheckoutController };
