import FormField from './FormField.vue';

export default {
    name: "LoginForm",
    components: {
        FormField
    },
    data() {
        return {
            username: "",
            password: "",
            error: "",
            isLoading: false,
            validationRules: {
                username: { required: true, minLength: 3 },
                password: { 
                    required: true, 
                    pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/,
                    message: "Password must be at least 8 characters and include letters and numbers"
                }
            }
        }
    },
    computed: {
        isValid() {
            return this.username.length >= 3 && 
                   this.password.match(this.validationRules.password.pattern);
        }
    },
    methods: {
        validateField(field) {
            const rules = this.validationRules[field];
            const value = this[field];

            if (rules.required && !value) {
                return `${field.charAt(0).toUpperCase() + field.slice(1)} is required`;
            }

            if (rules.minLength && value.length < rules.minLength) {
                return `${field.charAt(0).toUpperCase() + field.slice(1)} must be at least ${rules.minLength} characters`;
            }

            if (rules.pattern && !value.match(rules.pattern)) {
                return rules.message;
            }

            return "";
        },
        validateForm() {
            const usernameError = this.validateField("username");
            const passwordError = this.validateField("password");

            if (usernameError || passwordError) {
                this.error = usernameError || passwordError;
                return false;
            }

            this.error = "";
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
                this.error = error.response?.data?.message || 
                    error.response?.status === 401 ? "Invalid username or password" :
                    error.response?.status === 429 ? "Too many attempts. Please try again later" :
                    "Authentication failed. Please try again.";
            } finally {
                this.isLoading = false;
            }
        }
    },
    template: `
        <div class="container p-4 mx-auto max-w-md">
            <h1 class="text-2xl font-bold mb-6 text-center">Login to Your Account</h1>
            <form @submit.prevent="handleSubmit" class="space-y-6" novalidate>
                <FormField
                    v-model="username"
                    label="Username"
                    type="text"
                    :error="validateField('username')"
                    :disabled="isLoading"
                    autocomplete="username"
                />
                
                <FormField
                    v-model="password"
                    label="Password"
                    type="password"
                    :error="validateField('password')"
                    :disabled="isLoading"
                    autocomplete="current-password"
                />

                <div v-if="error" 
                    class="p-3 rounded bg-red-50 border border-red-200 text-red-600" 
                    role="alert"
                >
                    {{ error }}
                </div>

                <button 
                    type="submit" 
                    class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    :disabled="isLoading || !isValid"
                >
                    <span v-if="isLoading">
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Logging in...
                    </span>
                    <span v-else>Login</span>
                </button>
            </form>
        </div>
    `
}