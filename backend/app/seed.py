from sqlmodel import Session, select

from app.core.database import engine, init_db
from app.core.security import hash_password
from app.models.user import User
from app.models.company import Company
from app.models.product import Product
from app.models.delivery import DeliveryArea

BRAND = "Kabilai Dairy"

COMPANY_INFO = {
    "name": BRAND,
    "address": "123 Nungambakkam High Road, Chennai, Tamil Nadu 600034",
    "phone": "+91-44-28361234",
    "whatsapp_number": "919994333918",
    "intro_message": (
        "\U0001f9e0 *Kabilai Dairy on WhatsApp!* Namaste! I can help you pick dairy "
        "products, check prices, and confirm delivery. Say *stop ai* to reach a human."
    ),
    "ai_enabled": True,
}

PRODUCTS = [
    {"name": "Toned Milk", "category": "Fresh Milk", "unit": "500ml", "price": 26.0, "description": "Toned milk, low fat, pasteurized daily."},
    {"name": "Full Cream Milk", "category": "Fresh Milk", "unit": "500ml", "price": 32.0, "description": "Full cream milk for rich taste and nutrition."},
    {"name": "Cow Milk", "category": "Fresh Milk", "unit": "500ml", "price": 34.0, "description": "Fresh cow milk, delivered daily."},
    {"name": "Curd", "category": "Curd", "unit": "400g", "price": 30.0, "description": "Fresh set curd made every morning."},
    {"name": "Paneer", "category": "Paneer", "unit": "200g", "price": 70.0, "description": "Soft, fresh paneer. Best before 3 days."},
    {"name": "Ghee", "category": "Ghee", "unit": "500ml", "price": 450.0, "description": "Pure desi ghee, slow-cooked."},
    {"name": "Butter", "category": "Butter", "unit": "100g", "price": 60.0, "description": "Salted butter, churned fresh."},
]

CHENNAI_AREAS = [
    {"name": "T. Nagar", "pincode": "600017"},
    {"name": "Mylapore", "pincode": "600004"},
    {"name": "Anna Nagar", "pincode": "600040"},
    {"name": "Velachery", "pincode": "600042"},
    {"name": "Adyar", "pincode": "600020"},
    {"name": "Porur", "pincode": "600116"},
    {"name": "Tambaram", "pincode": "600045"},
    {"name": "Guindy", "pincode": "600032"},
]


def init_data() -> None:
    """Ensure tables exist and base data is present. Idempotent."""
    init_db()
    with Session(engine) as session:
        _seed_company(session)
        _seed_admin(session)
        _seed_products(session)
        _seed_delivery_areas(session)
        session.commit()


def seed() -> None:
    init_data()
    print("Seeding complete.")


def _seed_company(session: Session) -> None:
    existing = session.exec(select(Company).where(Company.name == BRAND)).first()
    if existing:
        print(f"Company '{BRAND}' already exists.")
        return
    session.add(Company(**COMPANY_INFO))
    print(f"Seeded company: {BRAND}")


ADMIN_EMAIL = "gopinath@kabilaifarm.com"
ADMIN_PASSWORD = "Gopinath@12345!"
ADMIN_NAME = "Gopinath"


def _seed_admin(session: Session) -> None:
    existing = session.exec(select(User).where(User.email == ADMIN_EMAIL)).first()
    if existing:
        if not existing.is_admin:
            existing.role = "admin"
            session.add(existing)
        print("Admin user already exists.")
        return
    user = User(
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        is_platform_admin=True,
        role="admin",
    )
    session.add(user)
    print(f"Seeded platform admin: {ADMIN_EMAIL}")


def _seed_products(session: Session) -> None:
    count = 0
    for data in PRODUCTS:
        existing = session.exec(select(Product).where(Product.name == data["name"])).first()
        if existing:
            continue
        session.add(Product(**data, is_available=True))
        count += 1
    print(f"Seeded {count} product(s).")


def _seed_delivery_areas(session: Session) -> None:
    count = 0
    for data in CHENNAI_AREAS:
        existing = session.exec(select(DeliveryArea).where(DeliveryArea.name == data["name"])).first()
        if existing:
            continue
        session.add(DeliveryArea(**data, city="Chennai", is_active=True))
        count += 1
    print(f"Seeded {count} delivery area(s).")


if __name__ == "__main__":
    seed()
