class UserService {
    constructor(database, userRepository) {
        this.database = database;
        this.userRepository = userRepository;
    }

    async deleteUser(userId) {
        await this.database.exec('BEGIN IMMEDIATE');
        try {
            await this.userRepository.deleteById(userId);
            await this.database.exec('COMMIT');
            return 'Usuário deletado com dados relacionados removidos.';
        } catch (error) {
            await this.database.exec('ROLLBACK');
            throw error;
        }
    }
}

module.exports = { UserService };
