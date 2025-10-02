import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

const registerSchema = z
  .object({
    name: z.string().min(2, 'Adınız en az 2 karakter olmalıdır'),
    email: z.string().email('Geçerli bir e-posta adresi girin'),
    password: z.string().min(8, 'Şifreniz en az 8 karakter olmalıdır'),
    confirmPassword: z.string(),
  })
  .superRefine(({ password, confirmPassword }, ctx) => {
    if (password !== confirmPassword) {
      ctx.addIssue({
        code: 'custom',
        message: 'Şifreler eşleşmiyor',
        path: ['confirmPassword'],
      });
    }
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export const RegisterPage = (): JSX.Element => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const inputClasses =
    'mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/40';

  const navigate = useNavigate();
  const registerUser = useAuthStore((state) => state.register);
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);
  const isLoading = useAuthStore((state) => state.isLoading);

  useEffect(() => clearError(), [clearError]);

  const onSubmit = async ({ name, email, password }: RegisterFormValues): Promise<void> => {
    try {
      await registerUser({ name, email, password });
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('Register failed', err);
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-8">
      <div className="space-y-2 text-center">
        <h1 className="text-3xl font-bold text-white">OrcaQuant ailesine katılın</h1>
        <p className="text-sm text-slate-400">Yapay zeka destekli tahminlere hemen erişin.</p>
      </div>
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-5 rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl"
      >
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-slate-300">
            Ad Soyad
          </label>
          <input id="name" type="text" {...register('name')} className={inputClasses} placeholder="Adınız Soyadınız" />
          {errors.name && <p className="mt-1 text-xs text-rose-400">{errors.name.message}</p>}
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-slate-300">
            E-posta
          </label>
          <input id="email" type="email" {...register('email')} className={inputClasses} placeholder="ornek@orcaquant.com" />
          {errors.email && <p className="mt-1 text-xs text-rose-400">{errors.email.message}</p>}
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-slate-300">
            Şifre
          </label>
          <input id="password" type="password" {...register('password')} className={inputClasses} placeholder="En az 8 karakter" />
          {errors.password && <p className="mt-1 text-xs text-rose-400">{errors.password.message}</p>}
        </div>
        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300">
            Şifre (Tekrar)
          </label>
          <input
            id="confirmPassword"
            type="password"
            {...register('confirmPassword')}
            className={inputClasses}
            placeholder="Şifrenizi tekrar girin"
          />
          {errors.confirmPassword && <p className="mt-1 text-xs text-rose-400">{errors.confirmPassword.message}</p>}
        </div>
        {error && <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div>}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? 'Kaydınız oluşturuluyor...' : 'Kayıt Ol'}
        </button>
        <p className="text-center text-sm text-slate-400">
          Zaten hesabınız var mı?{' '}
          <Link to="/login" className="text-accent hover:text-cyan-400">
            Giriş yapın
          </Link>
        </p>
      </form>
    </div>
  );
};
