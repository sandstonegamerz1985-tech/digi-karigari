"""Creates the tables and fills them with FICTIONAL sample data.

Run from the backend folder:
    python -m app.seed            # adds missing fictional sample products
    python -m app.seed --reset    # wipes everything and seeds again

All artisans and products below are made up for the demo. The product pictures are generated
placeholder images (SVG), not real photos.
"""
import html
import json
import secrets
import shutil
import sys
import textwrap

from . import models  # noqa: F401
from .config import settings
from .database import Base, SessionLocal, engine
from .models import (
    ArtisanProfile,
    Conversation,
    Dispute,
    DisputeAudit,
    DisputeMessage,
    Message,
    Notification,
    Order,
    OrderItem,
    Product,
    ProductImage,
    Review,
    TrustTierAudit,
    User,
    utcnow,
)
from .security import hash_password
from .services.trust_tier_service import compute_trust_tier, record_tier_change

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

# artisan key, title, description, category, price, stock, shipping, colours, materials, tags
PRODUCTS = [
    ("meera", "Madhubani Fish Painting on Handmade Paper",
     "A hand-painted Madhubani fish motif, drawn with fine brush lines and filled with natural colours on handmade paper. "
     "Fish stand for good luck in Mithila art. Unframed, ready to frame. Size about A4.",
     "Paintings", 1800, 5, 80, ("#b45309", "#7c2d12"), "Handmade paper, Natural pigment", "madhubani, folk art, painting, wall decor, gift"),
    ("meera", "Madhubani Tree of Life Wall Art",
     "A Tree of Life in traditional Madhubani style with birds and flowers, painted by hand with bold outlines and "
     "double borders. Paper is lightly textured and each piece differs a little.",
     "Paintings", 2400, 3, 80, ("#0f766e", "#134e4a"), "Handmade paper, Organic ink", "madhubani, tree of life, folk painting, living room"),
    ("ramesh", "Hand-painted Blue Pottery Planter",
     "A small round planter made in the Jaipur blue pottery style with a floral pattern in cobalt blue. "
     "Has a drainage hole. Glazed outside; handle with care.",
     "Pottery", 650, 12, 60, ("#1d4ed8", "#1e3a8a"), "Quartz clay, Glaze", "blue pottery, planter, ceramic, jaipur, balcony decor"),
    ("ramesh", "Terracotta Water Jug (Surahi)",
     "A traditional unglazed terracotta surahi that keeps water pleasantly cool. Wheel-thrown and fired by hand. "
     "Rinse before first use and air dry after cleaning.",
     "Pottery", 450, 20, 70, ("#c2410c", "#7c2d12"), "Natural Terracotta Clay", "terracotta, surahi, jug, earthen, kitchen"),
    ("ramesh", "Blue Pottery Tea Cup Set of 4",
     "Four small tea cups with matching floral designs in blue and white. Hand-painted, so patterns vary slightly. "
     "Hand wash recommended.",
     "Pottery", 1250, 8, 90, ("#2563eb", "#172554"), "Ceramic, Quartz glaze", "blue pottery, tea set, cups, dining, gift"),
    ("fatima", "Chikankari Cotton Dupatta",
     "A light cotton dupatta with hand-embroidered chikankari work along the border and corners. "
     "Soft and breathable. Gentle hand wash in cold water.",
     "Textiles", 1450, 10, 50, ("#be185d", "#831843"), "Pure Cotton, Cotton thread", "chikankari, dupatta, embroidery, handloom, summer"),
    ("fatima", "Chikankari Embroidered Table Runner",
     "A cotton table runner with delicate hand chikankari flowers. Fits a four to six seater table. "
     "Iron on low heat from the reverse side.",
     "Home Decor", 900, 7, 50, ("#7c3aed", "#4c1d95"), "Cotton, Hand embroidery", "table runner, chikankari, dining, decor"),
    ("fatima", "Block Print Cotton Scarf",
     "A soft cotton scarf printed with hand-carved wooden blocks in earthy colours. Light enough for all seasons. "
     "Colours may vary slightly between pieces.",
     "Textiles", 550, 25, 40, ("#15803d", "#14532d"), "Mulmul Cotton, Vegetable dye", "block print, scarf, cotton, handmade"),
    ("sanjay", "Sheesham Wood Carved Elephant",
     "A small elephant carved by hand from sheesham wood with a smooth natural finish. "
     "About 12 cm tall. (This listing appears in the shop after the admin approves Sanjay.)",
     "Woodwork", 1100, 6, 60, ("#92400e", "#451a03"), "Sheesham Wood", "wood carving, elephant, figurine, sheesham"),
    ("kavya", "Handmade Brass and Bead Earrings",
     "Lightweight earrings assembled by hand with brass hooks and hand-finished glass beads. "
     "Each pair has small variations because it is made one at a time.",
     "Jewellery", 780, 10, 40, ("#be123c", "#701a75"), "Brass, Handcrafted glass beads", "earrings, brass jewellery, beads, festive"),
    ("naseer", "Hand-hammered Brass Table Diya",
     "A small brass diya shaped and polished by hand in a family workshop. "
     "Wipe dry after use; use on a heat-safe surface.",
     "Metalcraft", 520, 15, 50, ("#b45309", "#78350f"), "Pure Brass", "diya, brass, pooja, diwali, festive, metalcraft"),
    ("anita", "Hand-stitched Leather Card Holder",
     "A compact card holder cut and stitched by hand from vegetable-tanned leather. "
     "Natural marks and color variation make each piece unique.",
     "Leather", 690, 8, 45, ("#a16207", "#422006"), "Vegetable-tanned leather", "leather, wallet, card holder, handcrafted"),
    ("bimal", "Woven Bamboo Storage Basket",
     "A small, lightweight storage basket woven by hand from bamboo strips. "
     "Suitable for dry household storage; each basket has a slightly different weave.",
     "Bamboo & Cane", 850, 9, 70, ("#65a30d", "#365314"), "Natural Bamboo", "bamboo, basket, woven, storage, eco-friendly"),
    ("vikram", "Hand-carved Sheesham Serving Tray",
     "A serving tray carved and sanded by hand from sheesham wood, with raised edges and a natural oil finish. "
     "Wipe clean with a dry cloth.",
     "Woodwork", 1350, 6, 80, ("#a16207", "#713f12"), "Sheesham Wood, Natural oil", "serving tray, woodwork, dining, sheesham"),
    ("fatima", "Block Print Cotton Stole",
     "A light cotton stole printed by hand with carved wooden blocks in a repeating leaf pattern. "
     "Soft enough for everyday wear. Wash separately in cold water; colours may soften a little over time.",
     "Textiles", 750, 14, 40, ("#0e7490", "#164e63"), "Cotton, Natural dye", "block print, stole, cotton, artisan"),
    ("kavya", "Beaded Layered Necklace",
     "A two-strand necklace strung by hand with glass beads and small brass spacers, closed with a simple hook clasp. "
     "Length is about 45 cm. Keep dry and store flat.",
     "Jewellery", 1150, 7, 40, ("#7e22ce", "#3b0764"), "Glass beads, Brass spacers", "necklace, beads, handmade jewellery, gift"),
    ("kavya", "Hand-twisted Brass Bangle Pair",
     "Two slim brass bangles twisted and filed smooth by hand. They are sold as a pair; each bangle differs very slightly. "
     "Wipe with a soft cloth to keep the shine.",
     "Jewellery", 640, 12, 40, ("#ca8a04", "#713f12"), "Solid Brass", "bangles, brass, hand-twisted, festive"),
    ("vikram", "Carved Sheesham Jewellery Box",
     "A small lidded box hand-carved from sheesham wood with a simple floral border and a natural oil finish. "
     "Lined with plain cotton cloth. Keep away from damp.",
     "Woodwork", 1650, 5, 80, ("#92400e", "#451a03"), "Sheesham Wood, Cotton lining", "jewellery box, sheesham, keepsake, woodcraft"),
    ("vikram", "Sheesham Wood Coaster Set of 4",
     "Four round coasters cut and sanded by hand from sheesham wood, each with a lightly carved edge. "
     "Grain and colour vary from piece to piece. Wipe clean; do not soak.",
     "Woodwork", 480, 18, 50, ("#b45309", "#78350f"), "Sheesham Wood", "coasters, sheesham, dining, drinkware"),
    ("meera", "Madhubani Peacock Painting on Handmade Paper",
     "A peacock painted by hand in the Madhubani style, with fine line work and natural-toned colours on handmade paper. "
     "Unframed and ready to frame. Size about A4; keep out of direct sun.",
     "Paintings", 2100, 4, 80, ("#0369a1", "#1e3a8a"), "Handmade paper, Mineral colours", "madhubani, peacock, traditional, wall art"),
    ("naseer", "Hand-polished Brass Bowl",
     "A small brass bowl shaped and polished by hand. Suitable for dry snacks or as a decorative piece. "
     "Hand wash and dry at once; a little lemon and salt restores the shine.",
     "Metalcraft", 890, 11, 60, ("#a16207", "#713f12"), "Brass", "brass bowl, metalcraft, snack bowl, dining"),
    ("naseer", "Brass Pooja Thali with Diya",
     "A round brass thali with a small matching diya, hammered and finished by hand. "
     "Use on a heat-safe surface. Wipe dry after cleaning.",
     "Metalcraft", 1450, 6, 70, ("#b45309", "#7c2d12"), "Hand-hammered Brass", "pooja thali, diya, diwali, metalcraft, ritual"),
    ("anita", "Hand-stitched Leather Passport Cover",
     "A slim passport cover cut and stitched by hand from vegetable-tanned leather with two card slots. "
     "The leather darkens naturally with use; small marks are part of the material.",
     "Leather", 820, 9, 45, ("#92400e", "#3f2305"), "Genuine Leather", "passport cover, travel, leather, gift"),
    ("anita", "Leather Bookmark Set of 3",
     "Three bookmarks cut and edge-finished by hand from leather offcuts, each with a stitched tassel. "
     "Colours differ a little between sets.",
     "Leather", 280, 25, 30, ("#a16207", "#44260a"), "Leather Offcuts", "bookmarks, reader gift, leather, stationery"),
    ("bimal", "Handwoven Cane Fruit Tray",
     "A shallow tray woven by hand from cane with a sturdy bamboo rim. Good for fruit or bread; "
     "wipe with a dry cloth and keep away from standing water.",
     "Bamboo & Cane", 720, 10, 70, ("#4d7c0f", "#1a2e05"), "Cane and Bamboo", "fruit tray, cane, bamboo, kitchen"),
    ("bimal", "Bamboo Table Mat Set of 4",
     "Four table mats woven by hand from thin bamboo strips. Lightweight and easy to store flat. "
     "Wipe clean with a dry cloth; weave patterns vary slightly.",
     "Bamboo & Cane", 540, 16, 60, ("#65a30d", "#3f6212"), "Bamboo strips", "table mats, dining, bamboo, natural"),
    ("ramesh", "Hand-painted Terracotta Diya Set of 6",
     "Six small terracotta diyas, wheel-made and painted by hand in warm festival colours. "
     "Colours and patterns vary between pieces. Use on a heat-safe surface.",
     "Home Decor", 420, 20, 60, ("#ea580c", "#7c2d12"), "Terracotta Clay", "diya set, diwali, festival, pottery, terracotta"),
    ("fatima", "Block Print Cotton Cushion Cover",
     "A 40 x 40 cm cotton cushion cover printed by hand with wooden blocks, closed with a hidden zip. "
     "Cover only, without the insert. Wash separately in cold water.",
     "Home Decor", 560, 13, 50, ("#9333ea", "#581c87"), "Cotton, Hand block print", "cushion cover, home decor, living room"),
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
        "Handmade Artisanal Craft · Digi Karigari</text></svg>"
    )


def ensure_seed_images() -> None:
    seed_dir = settings.UPLOAD_DIR / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    for n, (_key, title, _desc, _cat, _price, _stock, _ship, (c1, c2), _m, _t) in enumerate(PRODUCTS, start=1):
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
        had_existing_users = db.query(User).first() is not None
        demo_password_hash = hash_password(DEMO_PASSWORD) if not had_existing_users else None
        if not had_existing_users:
            db.add_all([
                User(name="Admin Asha", email="admin@digikarigari-demo.com",
                     password_hash=demo_password_hash, role="admin"),
                User(name="Buyer Bhavna", email="buyer@digikarigari-demo.com",
                     password_hash=demo_password_hash, role="buyer"),
                User(name="Buyer Rajesh", email="rajesh@digikarigari-demo.com",
                     password_hash=demo_password_hash, role="buyer"),
            ])

        existing_titles = {title for (title,) in db.query(Product.title).all()}
        missing_products = [item for item in PRODUCTS if item[1] not in existing_titles]
        required_artisans = {item[0] for item in missing_products}
        artisans: dict[str, User] = {}
        for key, name, email, craft, city, state, status, bio in ARTISANS:
            user = db.query(User).filter_by(email=email).first()
            if user is None:
                password_hash = demo_password_hash or hash_password(DEMO_PASSWORD)
                user = User(name=name, email=email, password_hash=password_hash, role="artisan")
                db.add(user)
            if user.artisan_profile is None:
                user.artisan_profile = ArtisanProfile(
                    craft=craft, city=city, state=state, bio=bio, status=status,
                    trust_tier="new_artisan" if status == "pending" else "verified_maker",
                )
            artisans[key] = user
        db.flush()

        buyer_bhavna = db.query(User).filter_by(email="buyer@digikarigari-demo.com", role="buyer").first()
        buyer_rajesh = db.query(User).filter_by(email="rajesh@digikarigari-demo.com", role="buyer").first()

        created: list[Product] = []
        for n, (key, title, desc, cat, price, stock, ship, (c1, c2), mats, tags) in enumerate(PRODUCTS, start=1):
            if title in existing_titles:
                continue
            filename = f"seed/product-{n}.svg"
            advisory = {
                "provider": "local_image_advisory_heuristic",
                "is_ai_powered": False,
                "disclaimer": "Advisory suggestion only. Human admin approval is final.",
                "overall_status": "ready_for_review",
                "checks": [
                    {"name": "Resolution", "status": "pass", "message": "Good 800x800 resolution vector."},
                    {"name": "Lighting & Brightness", "status": "pass", "message": "High-contrast palette."},
                    {"name": "Category Match", "status": "pass", "message": f"Accurate for {cat}."},
                ],
            }
            product = Product(
                artisan_id=artisans[key].id, title=title, description=desc, category=cat,
                price=price, stock=stock, shipping_fee=ship, ai_assisted=False,
                status="approved",
                materials=mats,
                tags=tags,
                ai_advisory_json=json.dumps(advisory),
            )
            product.images = [ProductImage(filename=filename, position=0)]
            db.add(product)
            created.append(product)
        db.flush()

        # Seed sample orders with delivered items and verified reviews
        p_fish = db.query(Product).filter(Product.title.like("%Fish Painting%")).first()
        p_planter = db.query(Product).filter(Product.title.like("%Blue Pottery Planter%")).first()
        p_surahi = db.query(Product).filter(Product.title.like("%Terracotta Water Jug%")).first()
        p_dupatta = db.query(Product).filter(Product.title.like("%Chikankari Cotton Dupatta%")).first()
        p_tray = db.query(Product).filter(Product.title.like("%Sheesham Serving Tray%")).first()

        now = utcnow()
        if buyer_bhavna and p_fish and not db.query(Order).filter_by(buyer_id=buyer_bhavna.id).first():
            # Order 1 (Delivered, with review)
            order1 = Order(
                buyer_id=buyer_bhavna.id, shipping_name="Bhavna Sharma", shipping_address="12 Lake Road, Sector 4",
                city="Delhi", pincode="110001", phone="9876543210", payment_status="paid_test", created_at=now,
            )
            item1 = OrderItem(
                product_id=p_fish.id, artisan_id=p_fish.artisan_id, title=p_fish.title,
                price=p_fish.price, shipping_fee=p_fish.shipping_fee, quantity=1,
                image="seed/product-1.svg", status="delivered", courier_name="India Post",
                tracking_id="IP987654321IN",
            )
            order1.items.append(item1)
            db.add(order1)
            db.flush()

            # Review for item 1
            rev1 = Review(
                product_id=p_fish.id, order_id=order1.id, order_item_id=item1.id,
                buyer_id=buyer_bhavna.id, artisan_id=p_fish.artisan_id,
                rating=5, title="Exquisite Madhubani artistry!",
                comment="The handmade paper texture and natural pigments are breathtaking. Arrived safely packaged.",
                status="published", created_at=now,
            )
            db.add(rev1)

            # Order 2 (In transit with planter & surahi)
            order2 = Order(
                buyer_id=buyer_bhavna.id, shipping_name="Bhavna Sharma", shipping_address="12 Lake Road, Sector 4",
                city="Delhi", pincode="110001", phone="9876543210", payment_status="paid_test", created_at=now,
            )
            item2 = OrderItem(
                product_id=p_planter.id, artisan_id=p_planter.artisan_id, title=p_planter.title,
                price=p_planter.price, shipping_fee=p_planter.shipping_fee, quantity=1,
                image="seed/product-3.svg", status="shipped", courier_name="Blue Dart",
                tracking_id="BD443210998",
            )
            order2.items.append(item2)
            db.add(order2)
            db.flush()

            # Seed a sample dispute on Order 2
            dispute = Dispute(
                order_id=order2.id, order_item_id=item2.id,
                buyer_id=buyer_bhavna.id, artisan_id=p_planter.artisan_id,
                reason="Damaged in transit",
                description="The package arrived slightly dented at corner. One small glaze chip near the planter rim.",
                requested_resolution="partial_refund", requested_amount=200,
                status="under_review", created_at=now,
            )
            db.add(dispute)
            db.flush()
            db.add(DisputeMessage(
                dispute_id=dispute.id, sender_id=buyer_bhavna.id, sender_role="buyer",
                message="Hello Ramesh ji, I received the planter today but noticed a small chip near the rim. Could we arrange a partial refund?",
                created_at=now,
            ))
            db.add(DisputeMessage(
                dispute_id=dispute.id, sender_id=p_planter.artisan_id, sender_role="artisan",
                message="Namaste Bhavna ji! I am so sorry to hear the courier mishandled it. I am very happy to accept the partial refund or send a replacement.",
                created_at=now,
            ))
            db.add(DisputeAudit(
                dispute_id=dispute.id, actor_id=buyer_bhavna.id, actor_role="buyer",
                action="dispute_opened", notes="Dispute opened for Damaged in transit (Rs 200 requested)",
                created_at=now,
            ))
            db.add(DisputeAudit(
                dispute_id=dispute.id, actor_id=p_planter.artisan_id, actor_role="artisan",
                action="artisan_responded", notes="Artisan agreed to resolution",
                created_at=now,
            ))

            # Conversation thread between Bhavna and Meera Devi
            convo = Conversation(
                buyer_id=buyer_bhavna.id, artisan_id=p_fish.artisan_id, product_id=p_fish.id,
                subject=f"Custom framing advice for {p_fish.title}",
                last_message_text="Thank you Meera ji! What type of glass framing do you recommend to preserve natural pigments?",
                last_message_at=now, created_at=now,
            )
            db.add(convo)
            db.flush()
            db.add(Message(
                conversation_id=convo.id, sender_id=buyer_bhavna.id,
                text="Namaste Meera ji! The fish painting arrived today and it is even more beautiful in person.",
                created_at=now,
            ))
            db.add(Message(
                conversation_id=convo.id, sender_id=p_fish.artisan_id,
                text="Dhanyawad Bhavna ji! So glad it reached you safely. I painted this during the Shravan festival.",
                created_at=now,
            ))
            db.add(Message(
                conversation_id=convo.id, sender_id=buyer_bhavna.id,
                text="Thank you Meera ji! What type of glass framing do you recommend to preserve natural pigments?",
                created_at=now,
            ))

            # Seed notification for Bhavna and Meera
            db.add(Notification(
                user_id=buyer_bhavna.id, type="order", title="Order #1 Delivered",
                message="Your Madhubani Fish Painting was delivered! Tap to leave a verified review.",
                link="/orders", created_at=now,
            ))
            db.add(Notification(
                user_id=p_fish.artisan_id, type="message", title="New message from Bhavna Sharma",
                message="Custom framing advice for Madhubani Fish Painting...",
                link=f"/messages?convo={convo.id}", created_at=now,
            ))

        # Additional review from Buyer Rajesh
        if buyer_rajesh and p_surahi:
            order3 = Order(
                buyer_id=buyer_rajesh.id, shipping_name="Rajesh Verma", shipping_address="45 Civil Lines",
                city="Jaipur", pincode="302001", phone="9823456789", payment_status="paid_test", created_at=now,
            )
            item3 = OrderItem(
                product_id=p_surahi.id, artisan_id=p_surahi.artisan_id, title=p_surahi.title,
                price=p_surahi.price, shipping_fee=p_surahi.shipping_fee, quantity=1,
                image="seed/product-4.svg", status="delivered", courier_name="Delhivery",
                tracking_id="DL77665544",
            )
            order3.items.append(item3)
            db.add(order3)
            db.flush()
            db.add(Review(
                product_id=p_surahi.id, order_id=order3.id, order_item_id=item3.id,
                buyer_id=buyer_rajesh.id, artisan_id=p_surahi.artisan_id,
                rating=5, title="Authentic cooling terracotta surahi",
                comment="Keeps water naturally cold with that fresh earthy fragrance. Beautiful traditional craft.",
                status="published", created_at=now,
            ))

        # Re-compute trust tiers for all seeded artisans
        all_profiles = db.query(ArtisanProfile).all()
        for prof in all_profiles:
            tier = compute_trust_tier(prof, db)
            if prof.user and prof.user.email == "meera@digikarigari-demo.com":
                tier = "master_artisan"  # Demo master artisan
                prof.manual_tier_override = "master_artisan"
                prof.override_reason = "Heritage Mithila master artist with outstanding cultural recognition."
            elif prof.user and prof.user.email == "ramesh@digikarigari-demo.com":
                tier = "trusted_artisan"
                prof.manual_tier_override = "trusted_artisan"
                prof.override_reason = "High fulfillment rate and positive customer feedback."
            prof.trust_tier = tier

        db.commit()

    print("Database seeded with sample products, reviews, trust tiers, messaging, and dispute cases.")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
