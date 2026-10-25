"""Creates the tables and fills them with FICTIONAL sample data.

Run from the backend folder:
    python -m app.seed            # seeds only if the database is empty
    python -m app.seed --reset    # wipes everything and seeds again

All artisans and products below are made up for the demo. The product pictures are generated
placeholder images (SVG), not real photos.
"""
import html
import shutil
import sys
import textwrap

from . import models  # noqa: F401
from .config import settings
from .database import Base, SessionLocal, engine
from .models import ArtisanProfile, Order, OrderItem, Product, ProductImage, User
from .security import hash_password

DEMO_PASSWORD = "demo1234"

ARTISANS = [
    # key, name, email, craft, city, state, status, bio
    ("meera", "Meera Devi", "meera@digikarigari-demo.com", "Madhubani painting", "Madhubani", "Bihar", "approved",
     "Meera learned Madhubani painting from her grandmother and now teaches village girls the craft. "
     "She paints with natural pigments on handmade paper."),
    ("ramesh", "Ramesh Kumhar", "ramesh@digikarigari-demo.com", "Pottery", "Jaipur", "Rajasthan", "approved",
     "Ramesh comes from a family of potters. He makes blue pottery and terracotta pieces on a hand-turned wheel."),
    ("fatima", "Fatima Begum", "fatima@digikarigari-demo.com", "Chikankari embroidery", "Lucknow", "Uttar Pradesh", "approved",
     "Fatima leads a small group of women who do fine chikankari hand embroidery on cotton and block-printed fabrics."),
    ("sanjay", "Sanjay Kumar", "sanjay@digikarigari-demo.com", "Wood carving", "Saharanpur", "Uttar Pradesh", "pending",
     "Sanjay carves small figures and boxes from sheesham wood. (Pending: log in as admin to approve him!)"),
]

# artisan key, title, description, category, price, stock, shipping, colours
PRODUCTS = [
    ("meera", "Madhubani Fish Painting on Handmade Paper",
     "A hand-painted Madhubani fish motif, drawn with fine brush lines and filled with natural colours on handmade paper. "
     "Fish stand for good luck in Mithila art. Unframed, ready to frame. Size about A4.",
     "Paintings", 1800, 5, 80, ("#b45309", "#7c2d12")),
    ("meera", "Madhubani Tree of Life Wall Art",
     "A Tree of Life in traditional Madhubani style with birds and flowers, painted by hand with bold outlines and "
     "double borders. Paper is lightly textured and each piece differs a little.",
     "Paintings", 2400, 3, 80, ("#0f766e", "#134e4a")),
    ("ramesh", "Hand-painted Blue Pottery Planter",
     "A small round planter made in the Jaipur blue pottery style with a floral pattern in cobalt blue. "
     "Has a drainage hole. Glazed outside; handle with care.",
     "Pottery", 650, 12, 60, ("#1d4ed8", "#1e3a8a")),
    ("ramesh", "Terracotta Water Jug (Surahi)",
     "A traditional unglazed terracotta surahi that keeps water pleasantly cool. Wheel-thrown and fired by hand. "
     "Rinse before first use and air dry after cleaning.",
     "Pottery", 450, 20, 70, ("#c2410c", "#7c2d12")),
    ("ramesh", "Blue Pottery Tea Cup Set of 4",
     "Four small tea cups with matching floral designs in blue and white. Hand-painted, so patterns vary slightly. "
     "Hand wash recommended.",
     "Pottery", 1250, 8, 90, ("#2563eb", "#172554")),
    ("fatima", "Chikankari Cotton Dupatta",
     "A light cotton dupatta with hand-embroidered chikankari work along the border and corners. "
     "Soft and breathable. Gentle hand wash in cold water.",
     "Textiles", 1450, 10, 50, ("#be185d", "#831843")),
    ("fatima", "Chikankari Embroidered Table Runner",
     "A cotton table runner with delicate hand chikankari flowers. Fits a four to six seater table. "
     "Iron on low heat from the reverse side.",
     "Home Decor", 900, 7, 50, ("#7c3aed", "#4c1d95")),
    ("fatima", "Block Print Cotton Scarf",
     "A soft cotton scarf printed with hand-carved wooden blocks in earthy colours. Light enough for all seasons. "
     "Colours may vary slightly between pieces.",
     "Textiles", 550, 25, 40, ("#15803d", "#14532d")),
    ("sanjay", "Sheesham Wood Carved Elephant",
     "A small elephant carved by hand from sheesham wood with a smooth natural finish. "
     "About 12 cm tall. (This listing appears in the shop after the admin approves Sanjay.)",
     "Woodwork", 1100, 6, 60, ("#92400e", "#451a03")),
]


def make_svg(title: str, c1: str, c2: str) -> str:
    lines = textwrap.wrap(title, 22)[:3]
    texts = "".join(
        f'<text x="400" y="{360 + i * 48}" text-anchor="middle" font-family="Georgia, serif" font-size="38" fill="#ffffff">{html.escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/>'
        f'<stop offset="1" stop-color="{c2}"/></linearGradient></defs>'
        '<rect width="800" height="800" fill="url(#g)"/>'
        '<circle cx="680" cy="120" r="150" fill="#ffffff" fill-opacity="0.08"/>'
        '<circle cx="90" cy="720" r="200" fill="#ffffff" fill-opacity="0.08"/>'
        f"{texts}"
        '<text x="400" y="700" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" fill="#ffffff" fill-opacity="0.8">'
        "Sample image - sellers upload real photos</text></svg>"
    )


def ensure_seed_images() -> None:
    """Writes the placeholder pictures for the sample products if they are missing."""
    seed_dir = settings.UPLOAD_DIR / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    for n, (_key, title, _desc, _cat, _price, _stock, _ship, (c1, c2)) in enumerate(PRODUCTS, start=1):
        path = seed_dir / f"product-{n}.svg"
        if not path.exists():
            path.write_text(make_svg(title, c1, c2), encoding="utf-8")


def run(reset: bool = False) -> None:
    products_dir = settings.UPLOAD_DIR / "products"
    if reset:
        Base.metadata.drop_all(engine)
        if products_dir.exists():
            shutil.rmtree(products_dir)
    products_dir.mkdir(parents=True, exist_ok=True)
    ensure_seed_images()
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if db.query(User).first():
            print("Database already has data. Use `python -m app.seed --reset` to start fresh.")
            return

        pw = hash_password(DEMO_PASSWORD)
        db.add_all([
            User(name="Admin Asha", email="admin@digikarigari-demo.com", password_hash=pw, role="admin"),
            User(name="Buyer Bhavna", email="buyer@digikarigari-demo.com", password_hash=pw, role="buyer"),
        ])

        artisans: dict[str, User] = {}
        for key, name, email, craft, city, state, status, bio in ARTISANS:
            user = User(name=name, email=email, password_hash=pw, role="artisan")
            user.artisan_profile = ArtisanProfile(craft=craft, city=city, state=state, bio=bio, status=status)
            db.add(user)
            artisans[key] = user
        db.flush()

        created: list[Product] = []
        for n, (key, title, desc, cat, price, stock, ship, (c1, c2)) in enumerate(PRODUCTS, start=1):
            filename = f"seed/product-{n}.svg"  # the picture file was written by ensure_seed_images()
            product = Product(
                artisan_id=artisans[key].id, title=title, description=desc, category=cat,
                price=price, stock=stock, shipping_fee=ship, ai_assisted=False,
            )
            product.images = [ProductImage(filename=filename, position=0)]
            db.add(product)
            created.append(product)
        db.flush()

        # One sample order so "Order history" is not empty on first login.
        buyer = db.query(User).filter_by(email="buyer@digikarigari-demo.com").one()
        painting = created[0]
        order = Order(
            buyer_id=buyer.id, shipping_name="Bhavna Sharma", shipping_address="12 Lake Road, Sector 4",
            city="Delhi", pincode="110001", phone="9876543210", payment_status="paid_test",
        )
        order.items.append(OrderItem(
            product_id=painting.id, artisan_id=painting.artisan_id, title=painting.title, price=painting.price,
            shipping_fee=painting.shipping_fee, quantity=1, image="seed/product-1.svg", status="shipped",
            courier_name="India Post (demo)", tracking_id="DEMO123456789",
        ))
        painting.stock -= 1
        db.add(order)
        db.commit()

    print("Seeded demo data. Demo password for every account:", DEMO_PASSWORD)
    print("  admin@digikarigari-demo.com   (admin)")
    print("  buyer@digikarigari-demo.com   (buyer)")
    print("  meera@ / ramesh@ / fatima@digikarigari-demo.com   (approved artisans)")
    print("  sanjay@digikarigari-demo.com  (artisan, PENDING approval)")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
