import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import DataTable from '../components/DataTable';
import { AdvancedFilters } from '../components/AdvancedFilters';
import { socket } from '../lib/socket';
import { queryClient } from '../lib/queryClient';
import { api } from '../lib/axios';
export default function UsersPage() {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [q, setQ] = useState('');
    const columns = useMemo(() => [
        { accessorKey: 'id', header: 'ID' },
        { accessorKey: 'email', header: 'E-posta' },
        { accessorKey: 'plan', header: 'Plan' },
        {
            accessorKey: 'status',
            header: 'Durum',
            cell: ({ getValue }) => {
                const value = getValue();
                const color = value === 'active' ? '#22c55e' : value === 'blocked' ? '#ef4444' : '#f97316';
                return <span style={{ color }}>{value}</span>;
            }
        },
        {
            accessorKey: 'created_at',
            header: 'Kayıt Tarihi',
            cell: ({ getValue }) => new Date(getValue()).toLocaleString('tr-TR')
        }
    ], []);
    const { data, isLoading, isError } = useQuery({
        queryKey: ['admin-users', { page, pageSize, q }],
        queryFn: async () => {
            const response = await api.get('/admin/users', {
                params: { page, page_size: pageSize, q }
            });
            return response.data;
        },
        keepPreviousData: true
    });
    useEffect(() => {
        const handleInvalidate = () => {
            queryClient.invalidateQueries({ queryKey: ['admin-users'] });
        };
        socket.on('admin:user.updated', handleInvalidate);
        socket.on('admin:user.deleted', handleInvalidate);
        return () => {
            socket.off('admin:user.updated', handleInvalidate);
            socket.off('admin:user.deleted', handleInvalidate);
        };
    }, []);
    function handleCsvExport() {
        const items = data?.items ?? [];
        if (!items.length) {
            toast('Aktarılacak kullanıcı yok');
            return;
        }
        const headers = ['ID', 'E-posta', 'Plan', 'Durum', 'Kayıt Tarihi'];
        const csvRows = [headers.join(',')];
        for (const user of items) {
            csvRows.push([user.id, user.email, user.plan, user.status, user.created_at.replace('T', ' ')].join(','));
        }
        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'users.csv';
        a.click();
        URL.revokeObjectURL(url);
    }
    function handleFiltersChange(filters) {
        const parts = [q, filters?.status, filters?.plan].filter(Boolean);
        setQ(parts.join(' '));
        setPage(1);
    }
    if (isLoading) {
        return <div className="p-6">Yükleniyor…</div>;
    }
    if (isError) {
        return <div className="p-6 text-red-400">Kullanıcılar alınamadı.</div>;
    }
    return (<div className="p-6 space-y-4">
      <h1 className="text-xl font-semibold">Kullanıcılar</h1>
      <div className="flex flex-wrap gap-2 items-center">
        <input className="input max-w-xs" placeholder="E-posta veya plan ara" value={q} onChange={(event) => {
            setQ(event.target.value);
            setPage(1);
        }}/>
        <button onClick={handleCsvExport} className="btn">
          CSV Dışa Aktar
        </button>
      </div>

      <AdvancedFilters onFiltersChange={handleFiltersChange}/>

      <DataTable data={data?.items || []} columns={columns} page={page} pageSize={pageSize} total={data?.total || 0} onPageChange={setPage} onPageSizeChange={(size) => {
            setPageSize(size);
            setPage(1);
        }}/>
    </div>);
}
