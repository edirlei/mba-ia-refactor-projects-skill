const { NotFoundError, ValidationError } = require('../errors/AppError');

class CheckoutService {
    constructor({
        database,
        userRepository,
        courseRepository,
        enrollmentRepository,
        paymentRepository,
        auditRepository,
        passwordService,
        paymentService,
        logger
    }) {
        this.database = database;
        this.userRepository = userRepository;
        this.courseRepository = courseRepository;
        this.enrollmentRepository = enrollmentRepository;
        this.paymentRepository = paymentRepository;
        this.auditRepository = auditRepository;
        this.passwordService = passwordService;
        this.paymentService = paymentService;
        this.logger = logger;
    }

    async checkout(command) {
        const course = await this.courseRepository.findActiveById(command.courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const paymentStatus = this.paymentService.authorize(command.cardNumber);
        await this.database.exec('BEGIN IMMEDIATE');
        try {
            let user = await this.userRepository.findByEmail(command.email);
            if (!user) {
                if (!command.password) {
                    throw new ValidationError('Senha é obrigatória para novo usuário');
                }
                const passwordHash = await this.passwordService.hash(command.password);
                user = await this.userRepository.create({
                    name: command.userName,
                    email: command.email,
                    passwordHash
                });
            }

            const enrollment = await this.enrollmentRepository.create(user.id, course.id);
            await this.paymentRepository.create(
                enrollment.id,
                course.price,
                paymentStatus
            );
            await this.auditRepository.record(
                `checkout course=${course.id} user=${user.id}`
            );
            await this.database.exec('COMMIT');
            this.logger.info('checkout_completed', { enrollmentId: enrollment.id });
            return { msg: 'Sucesso', enrollment_id: enrollment.id };
        } catch (error) {
            await this.database.exec('ROLLBACK');
            throw error;
        }
    }
}

module.exports = { CheckoutService };
