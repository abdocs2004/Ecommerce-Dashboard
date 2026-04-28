from database.connection import databaseConfig


def _ensure_products_category_column(cursor):
    cursor.execute("SHOW COLUMNS FROM PRODUCTS LIKE 'CATEGORY';")
    has_category_column = cursor.fetchone()

    if not has_category_column:
        cursor.execute(
            """
            ALTER TABLE PRODUCTS
            ADD COLUMN CATEGORY VARCHAR(100) NOT NULL DEFAULT 'General'
            AFTER DESCRIPTION;
            """
        )

        # Backfill readable category values for existing rows if CATEGORY_ID exists.
        cursor.execute("SHOW COLUMNS FROM PRODUCTS LIKE 'CATEGORY_ID';")
        has_category_id_column = cursor.fetchone()
        if has_category_id_column:
            cursor.execute(
                """
                UPDATE PRODUCTS
                SET CATEGORY = CONCAT('Category ', CATEGORY_ID)
                WHERE CATEGORY IS NULL OR CATEGORY = '';
                """
            )


# tables creation function defination
def createTables():

    # database connection access
    db_config = databaseConfig()
    cursor = db_config.cursor()

    users_table_query = """
        CREATE TABLE IF NOT EXISTS USERS (
        USERID BIGINT AUTO_INCREMENT PRIMARY KEY,

        NAME VARCHAR(100) NOT NULL,
        EMAIL VARCHAR(150) NOT NULL UNIQUE,
        PHONE_NUMBER VARCHAR(15) UNIQUE,

        PASSWORD VARCHAR(255) NOT NULL,

        PROFILE_IMAGE VARCHAR(255),   -- image path or URL

        ROLE ENUM('admin','user') DEFAULT 'admin',
        STATUS TINYINT(1) DEFAULT 1,

        CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP
    );"""


    cursor.execute(users_table_query)

    products_table_query = """
        CREATE TABLE IF NOT EXISTS PRODUCTS (
        PRODUCTID BIGINT AUTO_INCREMENT PRIMARY KEY,

        NAME VARCHAR(150) NOT NULL,
        DESCRIPTION TEXT,

        CATEGORY VARCHAR(100) NOT NULL,

        IMAGE_URL VARCHAR(255),   -- image path or CDN URL

        PRICE DECIMAL(10,2) NOT NULL CHECK (PRICE >= 0),
        STOCK INT DEFAULT 0 CHECK (STOCK >= 0),

        ACTIVE TINYINT(1) DEFAULT 1,

        CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ON UPDATE CURRENT_TIMESTAMP,

        INDEX idx_product_name (NAME),
        INDEX idx_category (CATEGORY),
        INDEX idx_active (ACTIVE)
    );"""
    
    cursor.execute(products_table_query)
    _ensure_products_category_column(cursor)
    # categories_table_query = """
    #     CREATE TABLE IF NOT EXISTS CATEGORIES (
    #     CATEGORY_ID BIGINT AUTO_INCREMENT PRIMARY KEY,
    #     CATEGORY_NAME VARCHAR(100) UNIQUE NOT NULL,
    #     ACTIVE TINYINT(1) DEFAULT 1
    # );
    # """
    # cursor.execute(categories_table_query)



    orders_table_query = """
        CREATE TABLE IF NOT EXISTS ORDERS (
        ID BIGINT AUTO_INCREMENT PRIMARY KEY,
        ORDER_ID BIGINT NOT NULL,          -- Same for all items in one order
        USER_ID BIGINT NOT NULL,
        PRODUCT_ID BIGINT NOT NULL,
        PRODUCT_NAME VARCHAR(100) NOT NULL,   -- snapshot at order time
        PRODUCT_PRICE DECIMAL(10,2) NOT NULL,
        QUANTITY INT NOT NULL DEFAULT 1,
        TOTAL_PRICE DECIMAL(12,2) GENERATED ALWAYS AS (PRODUCT_PRICE * QUANTITY) STORED,
        ORDER_STATUS ENUM('PENDING','DELIVERED', 'CANCELLED') DEFAULT 'PENDING',
        PAYMENT_METHOD ENUM('COD','UPI','CARD','NETBANKING'),
        PAYMENT_STATUS ENUM('PENDING','SUCCESS','FAILED') DEFAULT 'PENDING',
        CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
        );"""
    cursor.execute(orders_table_query)


    order_items_table_query = """CREATE TABLE IF NOT EXISTS ORDER_ITEMS (
        ID BIGINT AUTO_INCREMENT PRIMARY KEY,

        ORDERID BIGINT NOT NULL,
        PRODUCTID BIGINT NOT NULL,

        PRODUCTNAME VARCHAR(100) NOT NULL,
        PRODUCTPRICE DECIMAL(10,2) NOT NULL,

        QUANTITY INT NOT NULL DEFAULT 1,

        TOTALPRICE DECIMAL(12,2) 
            GENERATED ALWAYS AS (PRODUCTPRICE * QUANTITY) STORED
    );
    """
    cursor.execute(order_items_table_query)

    
    cart_table_query = """CREATE TABLE IF NOT EXISTS CART (
        CARTID BIGINT AUTO_INCREMENT PRIMARY KEY,
        USERID BIGINT NOT NULL,
        PRODUCTID BIGINT NOT NULL,
        QUANTITY INT NOT NULL DEFAULT 1,
        PRICE DECIMAL(10,2) NOT NULL,
        CREATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP,
        UPDATED_AT DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (USERID) REFERENCES USERS(USERID) ON DELETE CASCADE,
        FOREIGN KEY (PRODUCTID) REFERENCES PRODUCTS(PRODUCTID) ON DELETE CASCADE
    );"""
    cursor.execute(cart_table_query)
    db_config.commit()
    cursor.close()
    db_config.close()

    