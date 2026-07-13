const express = require('express');

const { ValidationError } = require('../errors/AppError');
const { asyncHandler } = require('../middlewares/asyncHandler');

function parseUserId(value) {
    const userId = Number(value);
    if (!Number.isInteger(userId) || userId <= 0) {
        throw new ValidationError('Usuário inválido');
    }
    return userId;
}

function createAdminRouter({ reportController, userController, requireAdmin }) {
    const router = express.Router();

    router.get(
        '/api/admin/financial-report',
        requireAdmin,
        asyncHandler(async (_request, response) => {
            const report = await reportController.financialReport();
            return response.status(200).json(report);
        })
    );

    router.delete(
        '/api/users/:id',
        requireAdmin,
        asyncHandler(async (request, response) => {
            const message = await userController.deleteUser(parseUserId(request.params.id));
            return response.status(200).send(message);
        })
    );

    return router;
}

module.exports = { createAdminRouter };
