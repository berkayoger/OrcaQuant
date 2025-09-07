"""
Basit seed: örnek admin/kullanıcı vb. oluşturma. CI'da idempotent çalışır.
Gerçek model isimlerinize göre uyarlayın.
"""
import os


def main():
    if not os.getenv("ORCAQUANT_SEED"):
        return
    try:
        # TODO: Projenizin gerçek ORM/migration yapısına göre seed yazın.
        # Örnek pseudo:
        # from backend.db import session
        # from backend.db.models import User
        # if not session.query(User).filter_by(email="admin@orcaquant.local").first():
        #     session.add(User(email="admin@orcaquant.local", username="admin"))
        #     session.commit()
        pass
    except Exception as exc:
        # Seed başarısız olsa bile deploy'u kırmamak için loglayıp devam edebilirsiniz.
        print(f"[seed_basic] seed atlandı/hata: {exc}")


if __name__ == "__main__":
    main()

