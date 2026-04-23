import { expect, test } from '@rstest/core';
import { render, screen } from '@testing-library/vue';
import App from '../src/App.vue';

test('renders the login screen when there is no active session', () => {
  render(App);
  expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument();
});
