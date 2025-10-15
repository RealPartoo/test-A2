# project/models.py
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

# Single MySQL instance (Flask-MySQLdb)
mysql = MySQL()

def init_models(app):
    """Call from create_app() after app.config is ready."""
    mysql.init_app(app)

def get_db():
    """Return the underlying MySQLdb connection."""
    return mysql.connection

def close_db(e=None):
    """Nothing required for Flask-MySQLdb; keep as a no-op."""
    # Connections are request-scoped; no manual close necessary.
    return None


# ---------------- Users ----------------
VALID_ROLES = {"admin", "customer", "artist", "gallery"}

def hash_password(raw: str) -> str:
    return generate_password_hash(raw)

def verify_password(stored_hash: str, raw: str) -> bool:
    return check_password_hash(stored_hash, raw)

def get_user_by_email(email: str):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT userId, userName, email, passwordHash, role, isDeleted
            FROM users
            WHERE email=%s AND isDeleted=0
            LIMIT 1
        """, (email.strip().lower(),))
        return cur.fetchone()

def get_user_by_id(user_id: int):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT userId, userName, email, passwordHash, role, isDeleted
            FROM users
            WHERE userId=%s AND isDeleted=0
            LIMIT 1
        """, (user_id,))
        return cur.fetchone()

def create_user(userName: str, email: str, password: str, role: str = "customer"):
    role = role if role in VALID_ROLES else "customer"
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO users (userName, email, passwordHash, role, isDeleted)
            VALUES (%s, %s, %s, %s, 0)
        """, (userName.strip(), email.strip().lower(), hash_password(password), role))
    db.commit()


# ---------------- Providers ----------------
def get_provider_by_user(user_id: int):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT providerId, userId, providerType, artistName, galleryName
            FROM providers
            WHERE userId=%s
            LIMIT 1
        """, (user_id,))
        return cur.fetchone()

def ensure_provider_for_user(user_id: int, role: str, display_name: str):
    """Create provider (Artist/Gallery) automatically if missing."""
    prov = get_provider_by_user(user_id)
    if prov:
        return prov
    providerType = "Artist" if role == "artist" else "Gallery"
    artistName   = display_name if providerType == "Artist" else None
    galleryName  = display_name if providerType == "Gallery" else None
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO providers(userId, providerType, artistName, galleryName)
            VALUES (%s, %s, %s, %s)
        """, (user_id, providerType, artistName, galleryName))
    db.commit()
    return get_provider_by_user(user_id)


# ---------------- Artworks ----------------
def create_artwork(provider_id: int, data: dict) -> int:
    """
    data keys: title, artistName, galleryName, type, genre, pricePerMonth (float),
               size, year, leaseStatus, imageUrl, description
    """
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO artworks
            (providerId, title, artistName, galleryName, type, genre, pricePerMonth,
             size, year, leaseStatus, imageUrl, description, isDeleted)
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
        """, (
            provider_id,
            data["title"], data["artistName"], data["galleryName"],
            data["type"], data["genre"], data["pricePerMonth"],
            data["size"], data["year"], data["leaseStatus"],
            data["imageUrl"], data["description"]
        ))
        new_id = cur.lastrowid
    db.commit()
    return new_id

def list_artworks(filters: dict) -> list:
    """
    filters: artist, gallery, type, genre, price, size, period, q, providerId(optional)
    """
    db = get_db()
    where, params = ["isDeleted=0"], []

    if filters.get("providerId"):
        where.append("providerId=%s"); params.append(filters["providerId"])
    if filters.get("artist"):
        where.append("artistName=%s"); params.append(filters["artist"])
    if filters.get("gallery"):
        where.append("galleryName=%s"); params.append(filters["gallery"])
    if filters.get("type"):
        where.append("type=%s"); params.append(filters["type"])
    if filters.get("genre"):
        where.append("genre=%s"); params.append(filters["genre"])
    if filters.get("q"):
        where.append("(title LIKE %s OR artistName LIKE %s OR galleryName LIKE %s)")
        q = f"%{filters['q']}%"
        params += [q, q, q]
    # price bucket
    if filters.get("price"):
        tag = filters["price"]
        if tag == "20000+":
            where.append("pricePerMonth >= 20000")
        else:
            s, e = tag.split("-")
            where.append("pricePerMonth BETWEEN %s AND %s")
            params += [float(s), float(e)]
    # size bucket (textual)
    if filters.get("size"):
        t = filters["size"]
        if t == "s":   where.append("size='Small ≤40cm'")
        if t == "m":   where.append("size='Medium 41–100cm'")
        if t == "l":   where.append("size='Large 101–180cm'")
        if t == "xl":  where.append("size='Oversize 180cm+'")
    # year/period
    if filters.get("period"):
        p = filters["period"]
        if p == "pre-1980": where.append("year='before 1980s'")
        elif p.endswith("0s"):
            where.append("year=%s"); params.append(p[:-1])  # '2020s' -> '2020'

    sql = f"""
      SELECT artworkId, providerId, title, artistName, galleryName, type, genre,
             pricePerMonth, size, year, leaseStatus, imageUrl, description
      FROM artworks
      WHERE {" AND ".join(where)}
      ORDER BY artworkId DESC
    """
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def get_artwork(artwork_id: int):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
          SELECT artworkId, providerId, title, artistName, galleryName, type, genre,
                 pricePerMonth, size, year, leaseStatus, imageUrl, description
          FROM artworks
          WHERE artworkId=%s AND isDeleted=0
          LIMIT 1
        """, (artwork_id,))
        return cur.fetchone()

def list_distinct_artists():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT artistName
            FROM artworks
            WHERE isDeleted=0 AND artistName IS NOT NULL AND artistName <> ''
            ORDER BY artistName
        """)
        return [r["artistName"] for r in cur.fetchall()]

def list_distinct_galleries():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT galleryName
            FROM artworks
            WHERE isDeleted=0 AND galleryName IS NOT NULL AND galleryName <> ''
            ORDER BY galleryName
        """)
        return [r["galleryName"] for r in cur.fetchall()]

# vendor helper
def list_artworks_by_provider(provider_id: int):
    return list_artworks({"providerId": provider_id})

def update_artwork(artwork_id: int, data: dict):
    """Update only fields provided in data."""
    if not data:
        return
    db = get_db()
    cols, params = [], []
    for k in ["title","artistName","galleryName","type","genre","pricePerMonth",
              "size","year","leaseStatus","imageUrl","description"]:
        if k in data:
            cols.append(f"{k}=%s")
            params.append(data[k])
    if not cols:
        return
    params.append(artwork_id)
    with db.cursor() as cur:
        cur.execute(f"UPDATE artworks SET {', '.join(cols)} WHERE artworkId=%s AND isDeleted=0", params)
    db.commit()

def delete_artwork(artwork_id: int):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE artworks SET isDeleted=1 WHERE artworkId=%s", (artwork_id,))
    db.commit()


# ---------------- Orders (write) ----------------
def create_order(user_id, contact: dict, shipping: dict, total_price: float) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO orders
              (userId, email, phone, recipientName, address, city, state, postcode, totalPrice)
            VALUES
              (%s,     %s,    %s,    %s,            %s,      %s,   %s,    %s,       %s)
            """,
            (
                user_id,
                contact.get("email"), contact.get("phone"),
                shipping.get("recipientName"), shipping.get("address"),
                shipping.get("city"), shipping.get("state"), shipping.get("postcode"),
                float(total_price or 0),
            ),
        )
        order_id = cur.lastrowid
    db.commit()
    return order_id

def add_order_items(order_id: int, cart_lines: list[dict]):
    if not cart_lines:
        return
    db = get_db()
    rows = []
    for line in cart_lines:
        rows.append((
            order_id,
            line.get("id"),
            line.get("title"),
            float(line.get("pricePerMonth") or 0),
            int(line.get("months") or 1),
            float(line.get("subtotal") or 0),
            line.get("imageUrl"),
        ))
    with db.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO order_items
              (orderId, artworkId, title, pricePerMonth, months, subtotal, imageUrl)
            VALUES
              (%s,      %s,        %s,    %s,            %s,     %s,       %s)
            """,
            rows,
        )
    db.commit()

def create_payment(card_number: str, exp_date: str, cvv: str) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO payments (cardNumber, expDate, cvv)
            VALUES (%s, %s, %s)
        """, (card_number, exp_date, cvv))
        pid = cur.lastrowid
    db.commit()
    return pid

def create_address(recipient_name: str, address: str, city: str, state: str, postcode: str) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO addresses (recipientName, address, city, state, postcode)
            VALUES (%s, %s, %s, %s, %s)
        """, (recipient_name, address, city, state, postcode))
        aid = cur.lastrowid
    db.commit()
    return aid

def create_order_row(user_id, email: str, phone: str, total_price, address_id: int, payment_id: int) -> int:
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO orders (userId, email, phoneNumber, totalPrice, addressId, paymentId)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, email, phone, float(total_price), address_id, payment_id))
        oid = cur.lastrowid
    db.commit()
    return oid

def add_order_item_row(order_id: int, artwork_id: int, image_url: str,
                       price_per_month, months: int, start_date, end_date, total_price):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO order_items
              (orderId, artworkId, imageUrl, pricePerMonth, startDate, endDate, months, TotalPrice)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id, artwork_id, image_url, float(price_per_month),
            start_date, end_date, months, float(total_price)
        ))
    db.commit()


# ---------------- Orders (read) ----------------
def list_orders_for_user(user_id: int) -> list:
    if not user_id:
        return []
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT orderId, totalPrice, orderDate
            FROM orders
            WHERE userId = %s
            ORDER BY orderDate DESC
        """, (user_id,))
        orders = cur.fetchall()

        for o in orders:
            cur.execute("""
                SELECT 
                    oi.orderItemId,
                    oi.artworkId,
                    oi.imageUrl,
                    oi.pricePerMonth,
                    oi.startDate,
                    oi.endDate,
                    oi.months,
                    oi.totalPrice,
                    a.title,
                    a.artistName,
                    a.galleryName
                FROM order_items oi
                JOIN artworks a ON a.artworkId = oi.artworkId
                WHERE oi.orderId = %s
                ORDER BY oi.orderItemId
            """, (o["orderId"],))
            o["items"] = cur.fetchall()
    return orders

def admin_list_orders():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT orderId, totalPrice, orderDate
            FROM orders
            ORDER BY orderDate DESC
        """)
        orders = cur.fetchall()

        for o in orders:
            cur.execute("""
                SELECT 
                    oi.orderItemId,
                    oi.artworkId,
                    oi.imageUrl,
                    oi.pricePerMonth,
                    oi.startDate,
                    oi.endDate,
                    oi.months,
                    oi.totalPrice,
                    a.title,
                    a.artistName,
                    a.galleryName
                FROM order_items oi
                JOIN artworks a ON a.artworkId = oi.artworkId
                WHERE oi.orderId = %s
                ORDER BY oi.orderItemId
            """, (o["orderId"],))
            o["items"] = cur.fetchall()
    return orders

def admin_list_artworks():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT artworkId, providerId, title, artistName, galleryName, type, genre,
                   pricePerMonth, size, year, leaseStatus, imageUrl, description
            FROM artworks
            WHERE isDeleted = 0
            ORDER BY updateDate DESC, artworkId DESC
        """)
        return cur.fetchall()

def admin_list_providers():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT 
                u.userId,
                u.userName,
                u.email,
                COALESCE(MIN(a.createDate), CURRENT_TIMESTAMP) AS createDate,
                COALESCE(p.galleryName, '') AS galleryName,
                COUNT(a.artworkId) AS artworkCount
            FROM users u
            LEFT JOIN providers p ON p.userId = u.userId
            LEFT JOIN artworks a 
                   ON a.providerId = p.providerId 
                  AND a.isDeleted = 0
            WHERE u.role IN ('artist','gallery')
            GROUP BY u.userId, u.userName, u.email, p.galleryName
            ORDER BY createDate DESC
        """)
        return cur.fetchall()

def list_my_artworks(user_id: int) -> list:
    """Artworks that belong only to this user (via providers)."""
    if not user_id:
        return []
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT a.artworkId, a.providerId, a.title, a.artistName, a.galleryName,
                   a.type, a.genre, a.pricePerMonth, a.size, a.year,
                   a.leaseStatus, a.imageUrl, a.description
            FROM artworks a
            JOIN providers p ON p.providerId = a.providerId
            WHERE p.userId = %s AND a.isDeleted = 0
            ORDER BY a.artworkId DESC
        """, (user_id,))
        return cur.fetchall()
