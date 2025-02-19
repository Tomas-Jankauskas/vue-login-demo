export default {
    name: "FormField",
    props: {
        modelValue: {
            type: String,
            required: true
        },
        label: {
            type: String,
            required: true
        },
        type: {
            type: String,
            default: "text"
        },
        error: {
            type: String,
            default: ""
        },
        disabled: {
            type: Boolean,
            default: false
        },
        autocomplete: {
            type: String,
            default: undefined
        }
    },
    computed: {
        inputId() {
            return `field-${this.label.toLowerCase().replace(/\s+/g, '-')}`;
        },
        hasError() {
            return Boolean(this.error);
        }
    },
    methods: {
        updateValue(event) {
            this.$emit('update:modelValue', event.target.value);
        }
    },
    template: `
        <div class="form-field">
            <label 
                :for="inputId"
                class="block text-sm font-medium text-gray-700 mb-1"
            >
                {{ label }}
            </label>
            
            <input
                :id="inputId"
                :type="type"
                :value="modelValue"
                @input="updateValue"
                :disabled="disabled"
                :autocomplete="autocomplete"
                :aria-invalid="hasError"
                :aria-describedby="hasError ? inputId + '-error' : undefined"
                class="block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                :class="{
                    'border-red-300 text-red-900 placeholder-red-300': hasError,
                    'border-gray-300': !hasError,
                    'opacity-50 cursor-not-allowed': disabled
                }"
            />
            
            <p 
                v-if="hasError"
                :id="inputId + '-error'"
                class="mt-1 text-sm text-red-600"
                role="alert"
            >
                {{ error }}
            </p>
        </div>
    `
}