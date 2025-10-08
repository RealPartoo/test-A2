from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import get_db

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
    """สร้าง provider (Artist/Gallery) อัตโนมัติ หากยังไม่มี"""
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
    filters: artist, gallery, type, genre, price_range(tag), size_tag, period_tag, q
    """
    db = get_db()
    where, params = ["isDeleted=0"], []

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
    # size bucket
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
        elif p.endswith("0s"): where.append("year=%s"); params.append(p[:-1])  # '2020s' -> '2020'

    sql = f"""
      SELECT artworkId, title, artistName, galleryName, type, genre,
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
