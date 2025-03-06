from app.extensions import db

class PDFSettings(db.Model):
    __tablename__ = 'pdf_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    font_path = db.Column(db.String(255), nullable=False, default='Dengb.ttf')
    font_size = db.Column(db.Integer, nullable=False, default=230)
    text_color = db.Column(db.String(20), nullable=False, default='255,0,0')  # RGB格式
    outline_color = db.Column(db.String(20), nullable=False, default='255,0,0')  # RGB格式
    outline_width = db.Column(db.Integer, nullable=False, default=0)
    position_x = db.Column(db.Integer, nullable=False, default=1500)
    position_y = db.Column(db.Integer, nullable=False, default=930)
    background_image = db.Column(db.String(255), nullable=False, default='bj.png')
    
    @property
    def text_color_tuple(self):
        return tuple(map(int, self.text_color.split(',')))
    
    @property
    def outline_color_tuple(self):
        return tuple(map(int, self.outline_color.split(',')))
    
    @property
    def position_tuple(self):
        return (self.position_x, self.position_y)
    
    def reset_to_default(self):
        """恢复默认设置"""
        self.font_path = 'Dengb.ttf'
        self.font_size = 230
        self.text_color = '255,0,0'
        self.outline_color = '255,0,0'
        self.outline_width = 0
        self.position_x = 1500
        self.position_y = 930
        self.background_image = 'bj.png' 