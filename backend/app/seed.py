"""Creates the tables and fills them with FICTIONAL sample data.

Run from the backend folder:
    python -m app.seed            # adds missing fictional sample products
    python -m app.seed --reset    # wipes everything and seeds again

All artisans and products below are made up for the demo. The product pictures are generated
placeholder images (SVG), not real photos.
"""
import html
import secrets
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
    ("kavya", "Kavya Shah", "kavya@digikarigari-demo.com", "Handmade jewellery", "Ahmedabad", "Gujarat", "approved",
     "Kavya makes small-batch bead and brass jewellery by hand in her home studio."),
    ("naseer", "Naseer Ali", "naseer@digikarigari-demo.com", "Metalcraft", "Moradabad", "Uttar Pradesh", "approved",
     "Naseer hand-hammers and finishes brassware using techniques learned in his family workshop."),
    ("anita", "Anita Devi", "anita@digikarigari-demo.com", "Leather craft", "Kanpur", "Uttar Pradesh", "approved",
     "Anita cuts and hand-stitches durable leather accessories in small batches."),
    ("bimal", "Bimal Das", "bimal@digikarigari-demo.com", "Bamboo and cane weaving", "Guwahati", "Assam", "approved",
     "Bimal weaves bamboo and cane homewares by hand using locally sourced materials."),
    ("vikram", "Vikram Singh", "vikram@digikarigari-demo.com", "Wood carving", "Saharanpur", "Uttar Pradesh", "approved",
     "Vikram hand-carves small homewares from responsibly sourced sheesham wood."),
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
    ("kavya", "Handmade Brass and Bead Earrings",
     "Lightweight earrings assembled by hand with brass hooks and hand-finished glass beads. "
     "Each pair has small variations because it is made one at a time.",
     "Jewellery", 780, 10, 40, ("#be123c", "#701a75")),
    ("naseer", "Hand-hammered Brass Table Diya",
     "A small brass diya shaped and polished by hand in a family workshop. "
     "Wipe dry after use; use on a heat-safe surface.",
     "Metalcraft", 520, 15, 50, ("#b45309", "#78350f")),
    ("anita", "Hand-stitched Leather Card Holder",
     "A compact card holder cut and stitched by hand from vegetable-tanned leather. "
     "Natural marks and color variation make each piece unique.",
     "Leather", 690, 8, 45, ("#a16207", "#422006")),
    ("bimal", "Woven Bamboo Storage Basket",
     "A small, lightweight storage basket woven by hand from bamboo strips. "
     "Suitable for dry household storage; each basket has a slightly different weave.",
     "Bamboo & Cane", 850, 9, 70, ("#65a30d", "#365314")),
    ("vikram", "Hand-carved Sheesham Serving Tray",
     "A serving tray carved and sanded by hand from sheesham wood, with raised edges and a natural oil finish. "
     "Wipe clean with a dry cloth.",
     "Woodwork", 1350, 6, 80, ("#a16207", "#713f12")),
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
        # Add only missing fictional sample listings. This is safe to run on every startup:
        # it never resets existing users, orders, or products.
        had_existing_users = db.query(User).first() is not None
        demo_password_hash = hash_password(DEMO_PASSWORD) if not had_existing_users else None
        if not had_existing_users:
            db.add_all([
                User(name="Admin Asha", email="admin@digikarigari-demo.com",
                     password_hash=demo_password_hash, role="admin"),
                User(name="Buyer Bhavna", email="buyer@digikarigari-demo.com",
                     password_hash=demo_password_hash, role="buyer"),
            ])

        existing_titles = {title for (title,) in db.query(Product.title).all()}
        missing_products = [item for item in PRODUCTS if item[1] not in existing_titles]
        required_artisans = {item[0] for item in missing_products}
        artisans: dict[str, User] = {}
        for key, name, email, craft, city, state, status, bio in ARTISANS:
            if key not in required_artisans:
                continue
            user = db.query(User).filter_by(email=email).first()
            if user and user.role != "artisan":
                raise RuntimeError(f"Demo artisan email is already used by a non-artisan account: {email}")
            if user is None:
                # On an existing database, keep these catalog-only accounts from becoming
                # login-able with the publicly documented demo password.
                password_hash = demo_password_hash or hash_password(secrets.token_urlsafe(32))
                user = User(name=name, email=email, password_hash=password_hash, role="artisan")
                db.add(user)
            if user.artisan_profile is None:
                user.artisan_profile = ArtisanProfile(
                    craft=craft, city=city, state=state, bio=bio, status=status
                )
            artisans[key] = user
        db.flush()
        buyer = db.query(User).filter_by(email="buyer@digikarigari-demo.com", role="buyer").first()

        created: list[Product] = []
        for n, (key, title, desc, cat, price, stock, ship, (c1, c2)) in enumerate(PRODUCTS, start=1):
            if title in existing_titles:
                continue
            filename = f"seed/product-{n}.svg"  # the picture file was written by ensure_seed_images()
            product = Product(
                artisan_id=artisans[key].id, title=title, description=desc, category=cat,
                price=price, stock=stock, shipping_fee=ship, ai_assisted=False,
            )
            product.images = [ProductImage(filename=filename, position=0)]
            db.add(product)
            created.append(product)
        db.flush()

        # Add a sample order only for a newly seeded sample product and demo buyer.
        painting = next((p for p in created if p.title == PRODUCTS[0][1]), None)
        if (painting is not None and buyer is not None
                and not db.query(Order).filter_by(buyer_id=buyer.id).first()):
            order = Order(
                buyer_id=buyer.id, shipping_name="Bhavna Sharma", shipping_address="12 Lake Road, Sector 4",
                city="Delhi", pincode="110001", phone="9876543210", payment_status="paid_test",
            )
            order.items.append(OrderItem(
                product_id=painting.id, artisan_id=painting.artisan_id, title=painting.title,
                price=painting.price, shipping_fee=painting.shipping_fee, quantity=1,
                image="seed/product-1.svg", status="shipped", courier_name="India Post (demo)",
                tracking_id="DEMO123456789",
            ))
            painting.stock -= 1
            db.add(order)
        db.commit()

    print(f"Added {len(created)} fictional handmade sample products with placeholder images.")
    if not had_existing_users:
        print("Demo password for the demo accounts:", DEMO_PASSWORD)
        print("  admin@digikarigari-demo.com   (admin)")
        print("  buyer@digikarigari-demo.com   (buyer)")
        print("  meera@ / ramesh@ / fatima@digikarigari-demo.com   (approved artisans)")
        print("  sanjay@digikarigari-demo.com  (artisan, PENDING approval)")
    else:
        print("Existing users and orders were preserved. No demo admin or buyer account was created.")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
