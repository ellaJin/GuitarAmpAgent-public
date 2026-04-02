
export const validatePassword = (pw: string): string | null => {
  const hasUpperCase = /[A-Z]/.test(pw);
  const hasLowerCase = /[a-z]/.test(pw);
  const hasNumbers = /\d/.test(pw);
  const hasNonalphas = /\W/.test(pw);
  const isLongEnough = pw.length >= 8;

  if (!isLongEnough || !hasUpperCase || !hasLowerCase || !hasNumbers || !hasNonalphas) {
    return "Password must be at least 8 characters long and include uppercase, lowercase, numbers, and special symbols.";
  }
  return null;
};