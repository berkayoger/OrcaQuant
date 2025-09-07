def test_import_backend_package():
    """
    Basit sağlık testi: 'backend' paketi import edilebilmeli.
    Böylece en azından modül bağımlılıkları ve __init__ hataları yakalanır.
    """
    __import__("backend")
    assert True

