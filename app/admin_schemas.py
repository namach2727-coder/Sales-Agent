from pydantic import BaseModel, Field, field_validator


class ManagerProductInput(BaseModel):
    client_id: str | None = Field(default=None, max_length=100)
    product_id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    price: float = Field(ge=0, le=10**15)
    is_available: bool = True
    keywords: list[str] = Field(default_factory=list, max_length=50)
    category: str | None = Field(default=None, max_length=200)
    aliases: list[dict[str, object]] = Field(default_factory=list, max_length=100)

    @field_validator("name", "description", "category")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            if len(cleaned) > 200:
                raise ValueError("هر کلمه کلیدی باید حداکثر ۲۰۰ نویسه باشد")
            result.append(cleaned)
        return result


class ManagerKnowledgeInput(BaseModel):
    client_id: str | None = Field(default=None, max_length=100)
    kind: str = Field(
        default="faq",
        pattern="^(faq|rule|shipping|payment|returns|warranty|policy|general)$",
    )
    title: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1, max_length=5000)
    keywords: list[str] = Field(default_factory=list, max_length=50)
    priority: int = Field(default=100, ge=0, le=1000)

    @field_validator("title", "answer")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("این مقدار نمی‌تواند خالی باشد")
        return cleaned

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            if len(cleaned) > 200:
                raise ValueError("هر کلمه کلیدی باید حداکثر ۲۰۰ نویسه باشد")
            result.append(cleaned)
        return result


class CatalogTrainingInput(BaseModel):
    store_name: str = Field(min_length=1, max_length=200)
    products: list[ManagerProductInput] = Field(min_length=1, max_length=200)
    knowledge_items: list[ManagerKnowledgeInput] = Field(default_factory=list, max_length=200)

    @field_validator("store_name")
    @classmethod
    def strip_store_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("نام فروشگاه نمی‌تواند خالی باشد")
        return cleaned


class AgentTestInput(BaseModel):
    message: str = Field(min_length=1, max_length=4096)


class ProductImageUploadInput(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    data_url: str = Field(min_length=100, max_length=12_000_000)


class ContentGenerateInput(BaseModel):
    product_id: int = Field(ge=1)
    media_asset_id: str = Field(min_length=36, max_length=36)


class ContentUpdateInput(BaseModel):
    caption: str = Field(min_length=1, max_length=2200)
    hashtags: list[str] = Field(default_factory=list, max_length=30)
    alt_text: str = Field(default="", max_length=1000)
    expected_revision: int = Field(ge=1)

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            if len(cleaned) > 100:
                raise ValueError("هر هشتگ باید حداکثر ۱۰۰ نویسه باشد")
            result.append(cleaned)
        return result


class ContentRevisionInput(BaseModel):
    expected_revision: int = Field(ge=1)


class ContentPublishInput(ContentRevisionInput):
    confirmation: str = Field(pattern="^publish$")


class StoreCreateInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=63)

    @field_validator("name", "slug")
    @classmethod
    def strip_store_fields(cls, value: str) -> str:
        return value.strip()


class StoreModuleUpdateInput(BaseModel):
    status: str = Field(pattern="^(inactive|trial|active|suspended)$")
    trial_days: int | None = Field(default=None, ge=1, le=90)
    custom_monthly_price_irr: int | None = Field(
        default=None, ge=0, le=10**12
    )


class ModulePriceUpdateInput(BaseModel):
    monthly_price_irr: int = Field(ge=0, le=10**12)
    setup_price_irr: int = Field(default=0, ge=0, le=10**12)
