const { ValidationError } = require('../errors/AppError');

class PaymentService {
    constructor(approvedPrefix) {
        this.approvedPrefix = approvedPrefix;
    }

    authorize(cardNumber) {
        if (!cardNumber.startsWith(this.approvedPrefix)) {
            throw new ValidationError('Pagamento recusado');
        }
        return 'PAID';
    }
}

module.exports = { PaymentService };
