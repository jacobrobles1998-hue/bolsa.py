from pydantic import BaseModel, Field


class SendMessageIn(BaseModel):
    profesional_id: int | None = None
    cliente_id: int | None = None
    texto: str = Field(min_length=1, max_length=2000)


class JoinConversationIn(BaseModel):
    profesional_id: int
    cliente_id: int
    limit: int | None = 50


class AuthLoginIn(BaseModel):
    email: str
    password: str


class AuthRegisterProfesionalIn(BaseModel):
    nombre: str
    email: str
    password: str
    telefono: str | None = None
    departamento: str | None = None
    ciudad: str | None = None
    genero: str | None = None
    edad: int | None = None
    altura: float | None = None
    peso: float | None = None
    especialidad: str | None = None
    universidad: str | None = None
    experiencia: int | None = None
    tarifa: float | None = None
    metodologia: str | None = None


class AuthRegisterClienteIn(BaseModel):
    nombre: str
    email: str
    password: str
    telefono: str | None = None
    departamento: str | None = None
    ciudad: str | None = None
    genero: str | None = None
    edad: int | None = None
    altura: float | None = None
    peso: float | None = None
    patologia_familiar: str | None = None
    metodologia: str | None = None


class FotoUpdateIn(BaseModel):
    foto_b64: str
    foto_mime: str | None = None


class CertCreateIn(BaseModel):
    titulo: str | None = None
    archivo_b64: str
    archivo_mime: str | None = None


class ProfileUpdateIn(BaseModel):
    cambios: dict


class ContratoCreateIn(BaseModel):
    profesional_id: int
    monto: float | None = None