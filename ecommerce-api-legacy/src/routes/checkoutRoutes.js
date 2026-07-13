const express = require('express');

const { asyncHandler } = require('../middlewares/asyncHandler');
const { parseCheckout } = require('../schemas/checkoutSchema');

function createCheckoutRouter(controller) {
    const router = express.Router();

    router.post(
        '/api/checkout',
        asyncHandler(async (request, response) => {
            const command = parseCheckout(request.body);
            const result = await controller.checkout(command);
            return response.status(200).json(result);
        })
    );

    return router;
}

module.exports = { createCheckoutRouter };
