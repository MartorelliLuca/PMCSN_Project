from interfaces.DeclarationValidator import DeclarationValidator

class DummyDeclarationValidator(DeclarationValidator):
    def validate(self, declaration_data: dict) -> bool:
        return "codice_fiscale" in declaration_data