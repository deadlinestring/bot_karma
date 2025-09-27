"""
Скрипт для инициализации базы данных с тестовыми данными
"""

from database import DatabaseManager, Category, Title, Product, Size, ProductSize

def init_test_data():
    """Инициализация базы данных с тестовыми данными"""
    
    with DatabaseManager.get_session() as db:
        # Очищаем существующие данные
        db.query(ProductSize).delete()
        db.query(Product).delete()
        db.query(Title).delete()
        db.query(Category).delete()
        db.query(Size).delete()
        db.commit()
        
        # Создаем категории
        categories_data = [
            {"name": "Аниме"},
            {"name": "Фильмы"},
            {"name": "Игры"},
            {"name": "Классика"}
        ]
        
        categories = []
        for cat_data in categories_data:
            category = Category(name=cat_data["name"])
            db.add(category)
            categories.append(category)
        
        db.commit()
        
        # Создаем тайтлы
        titles_data = [
            {"name": "Атака титанов", "category": "Аниме"},
            {"name": "Наруто", "category": "Аниме"},
            {"name": "Гарри Поттер", "category": "Фильмы"},
            {"name": "Властелин колец", "category": "Фильмы"},
            {"name": "Майнкрафт", "category": "Игры"},
            {"name": "The Witcher", "category": "Игры"},
            {"name": "Звездное небо", "category": "Классика"},
            {"name": "Луна и звезды", "category": "Классика"}
        ]
        
        titles = []
        for title_data in titles_data:
            category = next(cat for cat in categories if cat.name == title_data["category"])
            title = Title(name=title_data["name"], category_id=category.id)
            db.add(title)
            titles.append(title)
        
        db.commit()
        
        # Создаем размеры
        sizes_data = [
            {"name": "Мини 15см", "price": 1500},
            {"name": "Стандарт 25см", "price": 2500},
            {"name": "Большой 40см", "price": 3500},
            {"name": "Огромный 50см", "price": 4500}
        ]
        
        sizes = []
        for size_data in sizes_data:
            size = Size(name=size_data["name"], price=size_data["price"])
            db.add(size)
            sizes.append(size)
        
        db.commit()
        
        # Создаем товары
        products_data = [
            {"name": "Эрен Йегер", "title": "Атака титанов", "photo_url": None},
            {"name": "Микаса Аккерман", "title": "Атака титанов", "photo_url": None},
            {"name": "Леви", "title": "Атака титанов", "photo_url": None},
            {"name": "Наруто Узумаки", "title": "Наруто", "photo_url": None},
            {"name": "Саске Учиха", "title": "Наруто", "photo_url": None},
            {"name": "Какаши Хатаке", "title": "Наруто", "photo_url": None},
            {"name": "Гарри Поттер", "title": "Гарри Поттер", "photo_url": None},
            {"name": "Гермиона Грейнджер", "title": "Гарри Поттер", "photo_url": None},
            {"name": "Рон Уизли", "title": "Гарри Поттер", "photo_url": None},
            {"name": "Фродо Бэггинс", "title": "Властелин колец", "photo_url": None},
            {"name": "Гэндальф", "title": "Властелин колец", "photo_url": None},
            {"name": "Арагорн", "title": "Властелин колец", "photo_url": None},
            {"name": "Стив", "title": "Майнкрафт", "photo_url": None},
            {"name": "Крипер", "title": "Майнкрафт", "photo_url": None},
            {"name": "Геральт из Ривии", "title": "The Witcher", "photo_url": None},
            {"name": "Йеннифэр", "title": "The Witcher", "photo_url": None},
            {"name": "Цирилла", "title": "The Witcher", "photo_url": None},
            {"name": "Созвездие Большой Медведицы", "title": "Звездное небо", "photo_url": None},
            {"name": "Млечный путь", "title": "Звездное небо", "photo_url": None},
            {"name": "Полная луна", "title": "Луна и звезды", "photo_url": None},
            {"name": "Звездная ночь", "title": "Луна и звезды", "photo_url": None}
        ]
        
        products = []
        for product_data in products_data:
            title = next(title for title in titles if title.name == product_data["title"])
            product = Product(
                name=product_data["name"], 
                title_id=title.id, 
                photo_url=product_data["photo_url"]
            )
            db.add(product)
            products.append(product)
        
        db.commit()
        
        # Связываем товары с размерами (все товары со всеми размерами)
        for product in products:
            for size in sizes:
                product_size = ProductSize(product_id=product.id, size_id=size.id)
                db.add(product_size)
        
        db.commit()
        
        print("✅ База данных инициализирована с тестовыми данными!")
        print(f"📂 Создано категорий: {len(categories)}")
        print(f"📖 Создано тайтлов: {len(titles)}")
        print(f"🛍️ Создано товаров: {len(products)}")
        print(f"📏 Создано размеров: {len(sizes)}")
        print(f"🔗 Создано связей товар-размер: {len(products) * len(sizes)}")

if __name__ == "__main__":
    init_test_data()



