from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    id: int
    nome: str
    descricao: str
    preco: float
    estoque: int
    categoria: str
    ativo: int
    criado_em: str

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "preco": self.preco,
            "estoque": self.estoque,
            "categoria": self.categoria,
            "ativo": self.ativo,
            "criado_em": self.criado_em,
        }


@dataclass(frozen=True)
class User:
    id: int
    nome: str
    email: str
    tipo: str
    criado_em: str
    password_hash: str | None = None

    @classmethod
    def from_public_row(cls, row):
        return cls(**dict(row))

    @classmethod
    def from_auth_row(cls, row):
        values = dict(row)
        values["password_hash"] = values.pop("senha")
        return cls(**values)

    def to_public_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipo": self.tipo,
            "criado_em": self.criado_em,
        }

    def to_login_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipo": self.tipo,
        }


@dataclass(frozen=True)
class OrderItem:
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario: float

    def to_dict(self):
        return {
            "produto_id": self.produto_id,
            "produto_nome": self.produto_nome,
            "quantidade": self.quantidade,
            "preco_unitario": self.preco_unitario,
        }


@dataclass
class Order:
    id: int
    usuario_id: int
    status: str
    total: float
    criado_em: str
    itens: list[OrderItem] = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "status": self.status,
            "total": self.total,
            "criado_em": self.criado_em,
            "itens": [item.to_dict() for item in self.itens],
        }
