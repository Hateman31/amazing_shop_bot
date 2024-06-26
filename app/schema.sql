-- Создание таблицы "Заказы" (Orders)
CREATE TABLE Orders (
    order_id Serial PRIMARY KEY,
    customer_id BIGINT,
    order_date date,
    -- 1 -- заказ создан
    -- 2 -- заказ оплачен
    -- 3 -- заказ отменен
    status int default 1
    check (status = 1 or status = 2 or status = 3)
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
    customer_id BIGINT PRIMARY KEY
);

-- Создание таблицы "Товары" (Products)
CREATE TABLE Products (
    product_id Serial PRIMARY KEY,
    product_name TEXT,
    price DECIMAL(10, 2),
    is_active smallint default 1,
    category TEXT
    check (is_active = 1 or is_active = 2 )
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

insert into products(product_name, price, category)
values
		('Mafia 2',801, 'games'),
		('Assassin''s Creed II',2136, 'games'),
		('Battlefield 3',1088, 'games'),
		('World of Warcraft: Cataclysm',1634, 'games'),
		('World of Warcraft',661, 'games'),
		('Fortnite',1070, 'games'),
		('Euro Truck Simulator 2',2333, 'games');

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
select
    order_date
    , coalesce(full_price,0) full_price
    , customer_id
    , 'Order ' || (
            case status
                when 1 then 'created'
                when 2 then 'paid'
                else 'canceled'
            end) status
from Orders
left join main
	on Orders.order_id = main.order_id;