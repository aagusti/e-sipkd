from sqlalchemy import (
    Column,
    Index,
    Integer,
    SmallInteger,
    Text,
    BigInteger,
    String,
    Float,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint
    )
from   sqlalchemy.orm import relationship, backref
from ..models import(
      DBSession,
      DefaultModel,
      KodeModel,
      NamaModel,
      Base,
      User,
      CommonModel
      )
###########################
#
###########################        
class Pkb(DefaultModel,Base):
    __tablename__ = 'pkbs'
    id            = Column(BigInteger, primary_key=True)
    nik           = Column(String(16))
    no_rangka     = Column(String(16))
    email         = Column(String(32))
    mobile_phone  = Column(String(16))
    
class Pap(DefaultModel,Base):
    __tablename__ = 'paps'
    id            = Column(BigInteger, primary_key=True)
    no_skpd       = Column(String(16))
    email         = Column(String(32))
    mobile_phone  = Column(String(16))
    
class Unit(NamaModel,Base):
    __tablename__ = 'units'
    id            = Column(Integer, primary_key=True)
    kode          = Column(String(16), unique=True)
    nama          = Column(String(128))
    level_id      = Column(SmallInteger)
    is_summary    = Column(SmallInteger)
    parent_id     = Column(SmallInteger)
    
class Rekening(NamaModel,Base):
    __tablename__ = 'rekenings'
    id            = Column(Integer, primary_key=True)
    kode          = Column(String(24), unique=True)
    nama          = Column(String(128))
    level_id      = Column(SmallInteger)
    is_summary    = Column(SmallInteger)
    parent_id     = Column(SmallInteger)

class UnitRekening(Base):
    __tablename__ = 'unit_rekenings'
    id            = Column(Integer, primary_key=True)
    unit_id       = Column(Integer,ForeignKey("units.id"))
    rekening_id   = Column(Integer, ForeignKey("rekenings.id"))
    
class Jabatan(NamaModel, Base):
    __tablename__ = 'jabatans'
    status        = Column(Integer, default=1)
    UniqueConstraint('kode')    
    #nama = Column(String(128))
        
class Pegawai(NamaModel, Base):
    __tablename__ = 'pegawais'
    #nama        = Column(String(128))
    status        = Column(Integer, default=1)
    jabatan_id    = Column(Integer,ForeignKey("jabatans.id"))
    unit_id       = Column(Integer,ForeignKey("units.id"))
    user_id       = Column(Integer,ForeignKey("users.id"), nullable=True)
    users         = relationship("User", backref=backref('pegawais'))

    UniqueConstraint('kode')    
    
    @classmethod
    def get_by_user(cls, user_id):
        return DBSession.query(cls).filter(cls.user_id==user_id).all()
    
class PegawaiLogin(Base):
    __tablename__ = 'pegawai_users'
    user_id       = Column(Integer,ForeignKey("users.id"), primary_key=True)
    pegawai_id    = Column(Integer,ForeignKey("pegawais.id"), unique=True)
    change_unit   = Column(Integer,default=0, nullable=False)

class Pajak(NamaModel, Base):
    __tablename__     = 'pajaks'
    status            = Column(Integer, default=1)
    rekening_id       = Column(Integer,ForeignKey("rekenings.id"))
    tahun             = Column(Integer, nullable=False, default=0)
    tarif             = Column(Float, default=0, nullable=False)

    denda_rekening_id = Column(Integer, nullable=True, default=0)

    UniqueConstraint('rekening_id','tahun', name='rekening_tahun')
    rekenings         = relationship("Rekening", backref=backref('pajaks'))

class Wilayah(NamaModel,Base):
    __tablename__ = 'wilayahs'
    id            = Column(Integer, primary_key=True)
    kode          = Column(String(24), unique=True)
    nama          = Column(String(128))
    level_id      = Column(SmallInteger)
    parent_id     = Column(Integer, ForeignKey('wilayahs.id'), nullable=True)
    parent        = relationship("Wilayah",
                               backref="child",
                               remote_side=[id])
                        
class SubjekPajak(NamaModel, Base):
    __tablename__ = 'subjekpajaks'
    status        = Column(Integer, default=1)
    alamat_1      = Column(String(128))
    alamat_2      = Column(String(128))
    kelurahan     = Column(String(128))
    kecamatan     = Column(String(128))
    kota          = Column(String(128))
    user_id       = Column(Integer,ForeignKey("users.id"))
    users         = relationship("User", backref=backref('subjekpajaks'))
    
    UniqueConstraint('kode')
    
    # get_by_user untuk wp non global
    @classmethod
    def get_by_user_wp(cls, user_id):
        return DBSession.query(cls).filter_by(user_id=user_id).first()
        
    # get_by_user untuk wp global
    @classmethod
    def get_by_user(cls, user_id):
        return DBSession.query(cls).filter_by(user_id=user_id).all()
     
class ObjekPajak(NamaModel, Base):
    __tablename__  = 'objekpajaks'
    __table_args__ = (UniqueConstraint('subjekpajak_id', 'kode', 
                                       name='objekpajak_kode_uq'),)
    status         = Column(Integer, default=1)
    alamat_1       = Column(String(128))
    alamat_2       = Column(String(128))
    wilayah_id     = Column(Integer, ForeignKey("wilayahs.id"))
    unit_id        = Column(Integer, ForeignKey("units.id"))
    pajak_id       = Column(Integer, ForeignKey("pajaks.id"))
    subjekpajak_id = Column(Integer, ForeignKey("subjekpajaks.id")) 
    subjekpajaks   = relationship('SubjekPajak', backref=backref('objekpajaks'))
    pajaks         = relationship('Pajak', backref=backref('objekpajaks'))
    wilayahs       = relationship('Wilayah', backref=backref('objekpajaks'))
    units          = relationship('Unit', backref=backref('objekpajaks'))
    
class ARInvoice(CommonModel, Base):
    __tablename__   = 'arinvoices'
    id              = Column(Integer, primary_key=True)
    tahun_id        = Column(Integer)
    unit_id         = Column(Integer, ForeignKey("units.id"))
    no_id           = Column(Integer)
    subjek_pajak_id = Column(Integer, ForeignKey("subjekpajaks.id"))
    objek_pajak_id  = Column(Integer, ForeignKey("objekpajaks.id"))
    kode            = Column(String(32), unique=True)
    unit_kode       = Column(String(32))
    unit_nama       = Column(String(128))
    rekening_id     = Column(Integer, ForeignKey("rekenings.id"))
    rek_kode        = Column(String(16))    
    rek_nama        = Column(String(64))   
    wp_kode         = Column(String(16))
    wp_nama         = Column(String(64))
    wp_alamat_1     = Column(String(128))
    wp_alamat_2     = Column(String(128))
    op_kode         = Column(String(16))
    op_nama         = Column(String(64))
    op_alamat_1     = Column(String(128))
    op_alamat_2     = Column(String(128))
    dasar           = Column(BigInteger)
    tarif           = Column(Float)
    pokok           = Column(BigInteger)
    denda           = Column(BigInteger)
    bunga           = Column(BigInteger)
    jumlah          = Column(BigInteger)
    periode_1       = Column(Date)
    periode_2       = Column(Date)
    tgl_tetap       = Column(Date)
    jatuh_tempo     = Column(Date)
    status_bayar    = Column(SmallInteger, nullable=False, default=0) # 0 belum bayar 1 sudah bayar 2 batal
    owner_id        = Column(Integer)
    create_uid      = Column(Integer)
    update_uid      = Column(Integer)
    create_date     = Column(DateTime(timezone=True))
    update_date     = Column(DateTime(timezone=True))
    #bulan           = Column(Integer)
    #tanggal         = Column(Integer)
    subjekpajaks    = relationship("SubjekPajak", backref=backref('arinvoices'))
    objekpajaks     = relationship("ObjekPajak", backref=backref('arinvoices'))
    units           = relationship("Unit", backref=backref('arinvoices'))
    UniqueConstraint(tahun_id,unit_id,no_id,name='arinvoice_uq')
    
class ARSspd(CommonModel, Base):
    __tablename__ = 'arsspds'
    id            = Column(Integer, primary_key=True)
    tahun_id      = Column(Integer)
    unit_id       = Column(Integer, ForeignKey("units.id"))
    no_id         = Column(Integer)
    arinvoice_id  = Column(Integer, ForeignKey("arinvoices.id"))
    pembayaran_ke = Column(Integer)
    bunga         = Column(BigInteger)
    bayar         = Column(BigInteger)
    tgl_bayar     = Column(DateTime)
    posted        = Column(SmallInteger, nullable=False, default=0)
    create_uid    = Column(Integer)
    update_uid    = Column(Integer)
    create_date   = Column(DateTime(timezone=True))
    update_date   = Column(DateTime(timezone=True))
    arinvoices    = relationship("ARInvoice", backref=backref('arsspds'))
    units         = relationship("Unit", backref=backref('arsspds'))
    posted        = Column(SmallInteger, nullable=False, default=0)
    arinvoices    = relationship("ARInvoice", backref=backref('arsspds'))
    UniqueConstraint(arinvoice_id,pembayaran_ke,name='arsspd_uq')
    UniqueConstraint(tahun_id,unit_id,no_id,name='arsspd_no_uq')
                        
class ARSts(NamaModel,Base):
    __tablename__ = 'arsts'
    tahun_id      = Column(Integer)
    unit_id       = Column(Integer, ForeignKey("units.id"))
    tgl_sts       = Column(DateTime(timezone=True))
    unit_kode     = Column(String(32))
    unit_nama     = Column(String(128))
    no_id         = Column(Integer)
    virified      = Column(SmallInteger, nullable=False, default=0)
    posted        = Column(SmallInteger, nullable=False, default=0)
    create_uid    = Column(Integer)
    update_uid    = Column(Integer)
    create_date   = Column(DateTime(timezone=True))
    update_date   = Column(DateTime(timezone=True))
    status_bayar  = Column(SmallInteger)
    units         = relationship("Unit", backref=backref('arsts'))
    jumlah        = Column(BigInteger, nullable=False, default=0)
    UniqueConstraint(tahun_id,unit_id,no_id,name='arsts_no_uq')
    
class ARStsItem(Base):
    __tablename__ = 'arsts_item'
    sts_id        = Column(Integer, primary_key=True)
    sspd_id       = Column(Integer, ForeignKey('arsspds.id'),primary_key=True)
    rekening_id   = Column(Integer, ForeignKey('rekenings.id'), primary_key=True)
    jumlah        = Column(BigInteger, nullable=False, default=0)
    sspds         = relationship("ARSspd", backref=backref('arstsitems'))
    rekenings     = relationship("Rekening", backref=backref('arstsitems'))
    
class Param(Base):
    __tablename__ = 'params'
    id            = Column(Integer, primary_key=True)
    denda         = Column(Integer)
    jatuh_tempo   = Column(Integer)

    