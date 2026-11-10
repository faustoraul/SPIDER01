"""
Patrón Adaptador para integraciones con redes sociales.

REGLA DE NEGOCIO:
Cada red social tiene un formato de webhook diferente. Un adaptador
normaliza el payload entrante a un formato canónico de Lead.

INTEGRACIÓN REAL (futuro):
Solo se reemplaza la lógica interna de cada `*Adapter.parse_webhook()`.
No se modifica la base de datos, ni los servicios, ni las rutas.
Nunca se hardcodean endpoints ni permisos: deben verificarse en la
documentación oficial del proveedor antes de su implementación real.
"""

from ...core.exceptions import ValidationError


class BaseAdapter:
    provider = 'base'

    def parse_webhook(self, payload):
        """
        Recibe un dict crudo (payload del webhook) y devuelve:
        {
            'name': str,
            'email': str | None,
            'phone': str | None,
            'message': str | None,
        }
        o lanza ValidationError si no se puede procesar.
        """
        raise NotImplementedError

    def _require_name(self, payload):
        name = (payload.get('name') or '').strip()
        if not name:
            raise ValidationError(
                f"El webhook de {self.provider} no incluye un nombre de contacto válido."
            )
        return name


class FacebookAdapter(BaseAdapter):
    provider = 'facebook'

    def parse_webhook(self, payload):
        # Mock: en producción, parsear entry[0].changes[0].value.leadgen_id,
        # luego llamar a la Graph API para obtener el lead.
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


class InstagramAdapter(BaseAdapter):
    provider = 'instagram'

    def parse_webhook(self, payload):
        # Mock: en producción, parsear entry[0].messaging[0].sender.id
        # y consultar el perfil vía Instagram Graph API.
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


class WhatsappAdapter(BaseAdapter):
    provider = 'whatsapp'

    def parse_webhook(self, payload):
        # Mock: en producción, parsear entry[0].changes[0].value.messages[0]
        # y contacts[0].profile.name.
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


class MessengerAdapter(BaseAdapter):
    provider = 'messenger'

    def parse_webhook(self, payload):
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


class TiktokAdapter(BaseAdapter):
    provider = 'tiktok'

    def parse_webhook(self, payload):
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


class YoutubeAdapter(BaseAdapter):
    provider = 'youtube'

    def parse_webhook(self, payload):
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


class LinkedinAdapter(BaseAdapter):
    provider = 'linkedin'

    def parse_webhook(self, payload):
        name = self._require_name(payload)
        return {
            'name': name,
            'email': (payload.get('email') or '').strip() or None,
            'phone': (payload.get('phone') or '').strip() or None,
            'message': (payload.get('message') or '').strip() or None,
        }


_ADAPTERS = {
    'facebook': FacebookAdapter(),
    'instagram': InstagramAdapter(),
    'whatsapp': WhatsappAdapter(),
    'messenger': MessengerAdapter(),
    'tiktok': TiktokAdapter(),
    'youtube': YoutubeAdapter(),
    'linkedin': LinkedinAdapter(),
}


def get_adapter(provider):
    """Devuelve el adaptador correcto o lanza ValidationError."""
    adapter = _ADAPTERS.get(provider)
    if not adapter:
        raise ValidationError(
            f"Proveedor '{provider}' no soportado. "
            f"Disponibles: {', '.join(_ADAPTERS.keys())}."
        )
    return adapter