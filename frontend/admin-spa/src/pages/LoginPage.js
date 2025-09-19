import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/axios';
import { useAuthStore } from '../store/auth';
const schema = z.object({
    email: z.string().email('Geçerli bir e-posta girin'),
    password: z.string().min(6, 'Şifre en az 6 karakter olmalı')
});
export default function LoginPage() {
    const navigate = useNavigate();
    const login = useAuthStore((state) => state.login);
    const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) });
    const [isSubmitting, setIsSubmitting] = useState(false);
    async function onSubmit(values) {
        try {
            setIsSubmitting(true);
            const response = await api.post('/admin/auth/login', values);
            await login(response.data.token);
            navigate('/');
        }
        catch (error) {
            console.error(error);
        }
        finally {
            setIsSubmitting(false);
        }
    }
    return (<div className="min-h-screen flex items-center justify-center bg-neutral-950">
      <form onSubmit={handleSubmit(onSubmit)} className="card w-full max-w-md space-y-4">
        <header>
          <h1 className="text-2xl font-semibold">Yönetim Girişi</h1>
          <p className="text-sm text-neutral-400">Yetkili kullanıcılar için erişim.</p>
        </header>
        <div>
          <label className="block text-sm mb-1">E-posta</label>
          <input type="email" className="input" placeholder="admin@site.com" {...register('email')}/>
          {errors.email && <p className="text-sm text-red-400 mt-1">{errors.email.message}</p>}
        </div>
        <div>
          <label className="block text-sm mb-1">Şifre</label>
          <input type="password" className="input" placeholder="••••••••" {...register('password')}/>
          {errors.password && <p className="text-sm text-red-400 mt-1">{errors.password.message}</p>}
        </div>
        <button type="submit" className="btn w-full" disabled={isSubmitting}>
          {isSubmitting ? 'Giriş yapılıyor…' : 'Giriş Yap'}
        </button>
      </form>
    </div>);
}
