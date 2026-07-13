class UserController {
    constructor(userService) {
        this.userService = userService;
    }

    deleteUser(userId) {
        return this.userService.deleteUser(userId);
    }
}

module.exports = { UserController };
