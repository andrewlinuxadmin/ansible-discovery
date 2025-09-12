module.exports = {
  extends: ['@grafana/eslint-config'],
  root: true,
  rules: {
    'curly': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    'react-hooks/exhaustive-deps': 'warn',
    '@typescript-eslint/no-unused-vars': 'warn',
  },
};
