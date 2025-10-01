-- ===== Schema =====
CREATE TABLE IF NOT EXISTS users(
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','vendor','customer') NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories(
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS items(
  id INT AUTO_INCREMENT PRIMARY KEY,
  vendor_id INT, category_id INT,
  title VARCHAR(160), artist VARCHAR(160), gallery VARCHAR(160),
  type VARCHAR(80), genre VARCHAR(80),
  size VARCHAR(80), period VARCHAR(40),
  price DECIMAL(10,2), image_url VARCHAR(255),
  is_available BOOLEAN DEFAULT TRUE, description TEXT,
  FOREIGN KEY (vendor_id) REFERENCES users(id),
  FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS orders(
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT, order_type ENUM('lease','booking','purchase') NOT NULL DEFAULT 'lease',
  total DECIMAL(10,2) DEFAULT 0, status VARCHAR(40) DEFAULT 'CONFIRMED',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  full_name VARCHAR(160), phone VARCHAR(40), email VARCHAR(160),
  address_line VARCHAR(255), city VARCHAR(120), state VARCHAR(80), postcode VARCHAR(20),
  FOREIGN KEY (customer_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items(
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT, item_id INT, qty INT DEFAULT 1, price DECIMAL(10,2),
  lease_start DATE, lease_end DATE,
  FOREIGN KEY(order_id) REFERENCES orders(id),
  FOREIGN KEY(item_id) REFERENCES items(id)
);

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
