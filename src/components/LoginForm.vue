export default {
    name: "LoginForm",
    data() {
        return {
            username: "",
            password: "",
            error: ""
        }
    },
    methods: {
        async handleSubmit() {
            try {
                const response = await axios.post("/api/login", {
                    username: this.username,
                    password: this.password
                });
                
                if (response.data.success) {
                    this.$store.commit("setUser", response.data.user);
                    this.$emit("success", "Login successful!");
                }
            } catch (error) {
                this.error = "Something went wrong. Please try again.";
            }
        }
    },
    template: `
        <div class="container p-4 mx-auto">
            <h1 class="text-2xl font-bold mb-4">Login to Your Account</h1>
            <form @submit.prevent="handleSubmit" class="space-y-4">
                <div class="form-group">
                    <label class="block text-gray-700">Username:</label>
                    <input 
                        type="text"
                        v-model="username"
                        class="form-control"
                        placeholder="Enter your username"
                    >
                </div>
                <div class="form-group">
                    <label class="block text-gray-700">Password:</label>
                    <input 
                        type="password"
                        v-model="password"
                        class="form-control"
                        placeholder="Enter your password"
                    >
                </div>
                <div v-if="error" class="alert alert-danger">
                    {{ error }}
                </div>
                <button type="submit" class="btn btn-primary">
                    Login
                </button>
            </form>
        </div>
    `
}