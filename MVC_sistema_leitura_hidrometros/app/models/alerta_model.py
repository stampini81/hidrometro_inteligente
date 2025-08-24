from app import db
from datetime import datetime, timezone


class Alerta(db.Model):
    """Modelo para alertas de vazamento ou outras anomalias.

    Mantém registro histórico permitindo auditoria e fechamento (resolved_at).
    """
    __tablename__ = 'Alerta'

    id_alerta = db.Column(db.Integer, primary_key=True)
    dispositivo_id = db.Column(db.Integer, db.ForeignKey('Dispositivo.id_dispositivo'), nullable=True)
    serial = db.Column(db.String(100), index=True)
    tipo = db.Column(db.String(50), nullable=False, default='leak')
    message = db.Column(db.Text, nullable=False)
    threshold = db.Column(db.Float)
    flow_lmin = db.Column(db.Float)
    total_liters = db.Column(db.Float)
    duration_seconds = db.Column(db.Float)
    detected_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    def resolve(self):
        if not self.resolved_at:
            self.resolved_at = datetime.now(timezone.utc)
            return True
        return False

    def as_dict(self):
        return {
            'id': self.id_alerta,
            'dispositivo_id': self.dispositivo_id,
            'serial': self.serial,
            'tipo': self.tipo,
            'message': self.message,
            'threshold': self.threshold,
            'flow_lmin': self.flow_lmin,
            'total_liters': self.total_liters,
            'duration_seconds': self.duration_seconds,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }
