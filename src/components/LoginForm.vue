export default {
    name: "LoginForm",
    data() {
        return {
            username: "",
            password: "",
            error: "",
            isLoading: false
        }
    },
    methods: {
        validateForm() {
            if (!this.username || !this.password) {
                this.error = "Please fill in all fields";
                return false;
            }
            return true;
        },
        async handleSubmit() {
            if (!this.validateForm()) return;
            
            this.isLoading = true;
            try {
                const response = await axios.post("/api/login", {
                    username: this.username,
                    password: this.password
                }, {
                    headers: {
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                    }
                });
                
                if (response.data.success) {
                    this.$store.commit("setUser", response.data.user);
                    this.$emit("success", "Login successful!");
                }
            } catch (error) {
                this.error = error.response?.data?.message || "Authentication failed. Please try again.";
            } finally {
                this.isLoading = false;
            }
        }
    },
    template: `
        <div class="container p-4 mx-auto">
            <h1 class="text-2xl font-bold mb-4">Login to Your Account</h1>
            <form @submit.prevent="handleSubmit" class="space-y-4">
                <div class="form-group">
                    <label for="username" class="block text-gray-700">Username:</label>
                    <input 
                        id="username"
                        type="text"
                        v-model="username"
                        class="form-control"
                        placeholder="Enter your username"
                        aria-label="Username"
                        required
                    >
                </div>
                <div class="form-group">
                    <label for="password" class="block text-gray-700">Password:</label>
                    <input 
                        id="password"
                        type="password"
                        v-model="password"
                        class="form-control"
                        placeholder="Enter your password"
                        aria-label="Password"
                        pattern="^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$"
                        title="Password must be at least 8 characters and include letters and numbers"
                        required
                    >
                </div>
                <div v-if="error" class="alert alert-danger" role="alert">
                    {{ error }}
                </div>
                <button 
                    type="submit" 
                    class="btn btn-primary"
                    :disabled="isLoading"
                >
                    {{ isLoading ? 'Logging in...' : 'Login' }}
                </button>
            </form>
        </div>
    `
}