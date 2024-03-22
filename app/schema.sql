-- Создание таблицы "Заказы" (Orders)
CREATE TABLE Orders (
    order_id Serial PRIMARY KEY,
    customer_id INTEGER,
    order_date date
);

-- Создание таблицы "Товары в заказе" (Order_Items)
CREATE TABLE Order_Items (
    order_item_id Serial PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER
);

-- Создание таблицы "Клиенты" (Customers)
CREATE TABLE Customers (
    customer_id int PRIMARY KEY
);

-- Создание таблицы "Товары" (Products)
CREATE TABLE Products (
    product_id Serial PRIMARY KEY,
    product_name TEXT,
    price DECIMAL(10, 2),
    category TEXT
);

-- Вставка данных в таблицу "Товары"
INSERT INTO Products (product_id, product_name, price, category)
VALUES
    (201, 'Товар1', 10.00, 'Категория1'),
    (202, 'Товар2', 15.00, 'Категория2'),
    (203, 'Товар3', 20.00, 'Категория1'),
    (204, 'Товар4', 25.00, 'Категория2'),
    (205, 'Товар5', 30.00, 'Категория1'),
    (206, 'Товар6', 35.00, 'Категория2');


-- drop view Orders_history_vw;
-- select * from Orders_history_vw
create view Orders_history_vw as
with main as (
	select order_id, sum(price*quantity) full_price
	from Order_items oims
	join Products p
		on p.product_id = oims.product_id
	group by order_id
)
select order_date, coalesce(full_price,0) full_price, customer_id
from Orders
left join main
	on Orders.order_id = main.order_id;