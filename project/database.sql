-- project/database.sql
-- Target: MySQL 8, utf8mb4
-- Database name ตามที่คุณใช้: IFN582_Database

DROP DATABASE IF EXISTS IFN582_Database;
CREATE DATABASE IF NOT EXISTS IFN582_Database
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE IFN582_Database;

-- ========== USERS ==========
-- role: 'admin','customer','artist', 'gallery'
CREATE TABLE users (
  userId            INT AUTO_INCREMENT PRIMARY KEY,
  userName      VARCHAR(50)  NOT NULL UNIQUE,
  email         VARCHAR(120) NOT NULL UNIQUE,
  passwordHash VARCHAR(255) NOT NULL,
  role          ENUM('admin','customer','artist', 'gallery') NOT NULL,
  createdAt    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  isDeleted TINYINT NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- ========== PROVIDERS (Artists/Galleries owned by vendor users) ==========
CREATE TABLE providers (
  providersId            INT AUTO_INCREMENT PRIMARY KEY,
  userId       INT NOT NULL,
  providerType ENUM('Artist','Gallery') NOT NULL,
  artistName    VARCHAR(100),
  galleryName   VARCHAR(100),
  CONSTRAINT fk_provider_user
    FOREIGN KEY (userId) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ========== CUSTOMERS ==========
CREATE TABLE customers (
  customerId      INT AUTO_INCREMENT PRIMARY KEY,
  userId INT NOT NULL,
  CONSTRAINT fk_customer_user
    FOREIGN KEY (userId) REFERENCES users(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ========== ADDRESSES (ใช้กับ Order) ==========
CREATE TABLE addresses (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  address       VARCHAR(255) NOT NULL,
  city          VARCHAR(100) NOT NULL,
  state         VARCHAR(50)  NOT NULL,
  postcode      VARCHAR(20)  NOT NULL,
  recipientName VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- ========== PAYMENTS (mock) ==========
CREATE TABLE payments (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  cardNumber VARCHAR(50)  NOT NULL,
  expDate    VARCHAR(10)  NOT NULL,
  cvv        VARCHAR(10)  NOT NULL
) ENGINE=InnoDB;

-- ========== ARTWORKS ==========
-- leaseStatus: 'Available' | 'Unavailable'
CREATE TABLE artworks (
  artworkId             INT AUTO_INCREMENT PRIMARY KEY,
  providerId    INT NOT NULL,
  title          VARCHAR(200) NOT NULL,
  artistName     VARCHAR(100) NOT NULL,
  galleryName    VARCHAR(100) NULL,
  type           ENUM('Oil Painting', 'Pastel Painting', 'Watercolor Painting', 'Acrylic Painting', 'Digital Painting') NOT NULL,
  genre          VARCHAR(50)  NOT NULL,
  pricePerMonth  DECIMAL(10,2) NOT NULL,
  size           VARCHAR(50)  NOT NULL,
  year           ENUM('before 1980s','1980s', '1990s', '2000', '2010', '2020', '2021', '2022', '2023', '2024', '2025') NOT NULL,
  leaseStatus    ENUM('Available','Unavailable') NOT NULL DEFAULT 'Available',
  imageUrl       VARCHAR(255) NOT NULL,
  description    TEXT,
  createDate     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updateDate     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  isDeleted TINYINT NOT NULL DEFAULT 0,
  CONSTRAINT fk_artwork_provider
    FOREIGN KEY (provider_id) REFERENCES providers(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_artworks_status ON artworks(leaseStatus);
CREATE INDEX idx_artworks_genre  ON artworks(genre);
CREATE INDEX idx_artworks_type   ON artworks(type);

-- ========== CARTS ==========
CREATE TABLE carts (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  userId INT NOT NULL,
  createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_cart_customer
    FOREIGN KEY (userId) REFERENCES customers(id)
    ON DELETE CASCADE
) ENGINE=InnoDB;

-- ========== CART ITEMS ==========
CREATE TABLE cart_items (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  cartId       INT NOT NULL,
  artworkId    INT NOT NULL,
  imageUrl      VARCHAR(255) NOT NULL,
  pricePerMonth DECIMAL(10,2) NOT NULL,
  startDate     DATE NOT NULL,
  endDate       DATE NOT NULL,
  months        DECIMAL(6,2) NOT NULL,
  totalPrice    DECIMAL(12,2) NOT NULL,
  createDate    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updateDate    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  isDeleted TINYINT NOT NULL DEFAULT 0,
  CONSTRAINT fk_ci_cart    FOREIGN KEY (cart_id)    REFERENCES carts(id)     ON DELETE CASCADE,
  CONSTRAINT fk_ci_artwork FOREIGN KEY (artwork_id) REFERENCES artworks(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ========== ORDERS ==========
CREATE TABLE orders (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  userId INT NOT NULL,
  email       VARCHAR(100) NOT NULL,
  phoneNumber VARCHAR(50)  NOT NULL,
  totalPrice  DECIMAL(12,2) NOT NULL,
  orderDate   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  addressId   INT NOT NULL,
  paymentId   INT NOT NULL,
  CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
  CONSTRAINT fk_order_address  FOREIGN KEY (addressId)   REFERENCES addresses(id) ON DELETE RESTRICT,
  CONSTRAINT fk_order_payment  FOREIGN KEY (paymentId)   REFERENCES payments(id)  ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ========== ORDER ITEMS ==========
CREATE TABLE order_items (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  orderId       INT NOT NULL,
  artworkId     INT NOT NULL,
  imageUrl      VARCHAR(255) NOT NULL,
  pricePerMonth DECIMAL(10,2) NOT NULL,
  startDate     DATE NOT NULL,
  endDate       DATE NOT NULL,
  months        DECIMAL(6,2) NOT NULL,
  totalPrice    DECIMAL(12,2) NOT NULL,
  createDate    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_oi_order   FOREIGN KEY (orderId)   REFERENCES orders(id)   ON DELETE CASCADE,
  CONSTRAINT fk_oi_artwork FOREIGN KEY (artworkId) REFERENCES artworks(id) ON DELETE RESTRICT
) ENGINE=InnoDB;



-- ===== Seeds (แก้รหัสผ่านเป็น hash จริงภายหลัง) =====
INSERT IGNORE INTO users (id,name,email,password_hash,role) VALUES
  (1,'Admin One','admin1@example.com','$pbkdf2-sha256$dummy','admin'),
  (2,'Admin Two','admin2@example.com','$pbkdf2-sha256$dummy','admin'),
  (3,'Vendor One','vendor1@example.com','$pbkdf2-sha256$dummy','vendor'),
  (4,'Vendor Two','vendor2@example.com','$pbkdf2-sha256$dummy','vendor'),
  (5,'Cust One','cust1@example.com','$pbkdf2-sha256$dummy','customer'),
  (6,'Cust Two','cust2@example.com','$pbkdf2-sha256$dummy','customer');

INSERT IGNORE INTO categories (id,name) VALUES
  (1,'Paintings'), (2,'Sculptures');

INSERT IGNORE INTO items
(vendor_id,category_id,title,artist,gallery,type,genre,size,period,price,image_url,description,is_available)
VALUES
 (3,1,'Sunset Fields','A. Rivera','Gallery North','Oil Painting','Illustrative','40x60','2021',120.00,'img/placeholder.jpg','Warm sunset tone', TRUE),
 (4,1,'Blue Portrait','K. Lin','Gallery West','Acrylic Painting','Portrait','50x70','2020',150.00,'img/placeholder.jpg','Cool portrait', TRUE);

-- สร้าง items ให้ครบ >=15 ชิ้นก่อนเดโม (คัดลอกแถวข้างบนแล้วแก้ค่าบางส่วน)
