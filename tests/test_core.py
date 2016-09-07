import unittest
import hashlib
from hashlib import sha512

from construct import *
from construct.lib.py3compat import PY26


class TestStruct(unittest.TestCase):
    def test_build_from_nested_dicts(self):
        s = Struct(None, Struct('substruct1', Byte('field1')))
        self.assertEqual(s.build(dict(substruct1=dict(field1=5))), b'\x05')


class TestStaticField(unittest.TestCase):

    def setUp(self):
        self.sf = StaticField("staticfield", 2)

    def test_trivial(self):
        pass

    def test_parse(self):
        self.assertEqual(self.sf.parse(b"ab"), b"ab")

    def test_build(self):
        self.assertEqual(self.sf.build(b"ab"), b"ab")

    def test_parse_too_short(self):
        self.assertRaises(FieldError, self.sf.parse, b"a")

    def test_build_too_short(self):
        self.assertRaises(FieldError, self.sf.build, b"a")

    def test_sizeof(self):
        self.assertEqual(self.sf.sizeof(), 2)

    def test_field_parse(self):
        f = Field('name', 6)
        self.assertEqual(f.parse(b'abcdef'), b'abcdef')
        self.assertEqual(f.parse(b'12abcdef'), b'12abcd')
        

class TestFormatField(unittest.TestCase):

    def setUp(self):
        self.ff = FormatField("formatfield", "<", "L")

    def test_trivial(self):
        pass

    def test_parse(self):
        self.assertEqual(self.ff.parse(b"\x12\x34\x56\x78"), 0x78563412)

    def test_build(self):
        self.assertEqual(self.ff.build(0x78563412), b"\x12\x34\x56\x78")

    def test_parse_too_short(self):
        self.assertRaises(FieldError, self.ff.parse, b"\x12\x34\x56")

    def test_build_too_long(self):
        if not PY26:
            self.assertRaises(FieldError, self.ff.build, 2**100)

    def test_build_wrong_value(self):
        self.assertRaises(FieldError, self.ff.build, 9e9999)
        self.assertRaises(FieldError, self.ff.build, "string not int")

    def test_sizeof(self):
        self.assertEqual(self.ff.sizeof(), 4)


class TestMetaField(unittest.TestCase):

    def setUp(self):
        self.mf = MetaField("metafield", lambda ctx: 3)

    def test_trivial(self):
        pass

    def test_parse(self):
        self.assertEqual(self.mf.parse(b"abc"), b"abc")

    def test_build(self):
        self.assertEqual(self.mf.build(b"abc"), b"abc")

    def test_parse_too_short(self):
        self.assertRaises(FieldError, self.mf.parse, b"ab")

    def test_build_too_short(self):
        self.assertRaises(FieldError, self.mf.build, b"ab")

    def test_sizeof(self):
        self.assertEqual(self.mf.sizeof(), 3)


class TestMetaFieldStruct(unittest.TestCase):

    def setUp(self):
        self.mf = MetaField("data", lambda ctx: ctx.length)
        self.s = Struct("struct", Byte("length"), self.mf)

    def test_trivial(self):
        pass

    def test_parse(self):
        c = self.s.parse(b"\x03ABC")
        self.assertEqual(c.length, 3)
        self.assertEqual(c.data, b"ABC")

        c = self.s.parse(b"\x04ABCD")
        self.assertEqual(c.length, 4)
        self.assertEqual(c.data, b"ABCD")

    def test_sizeof_default(self):
        print("NOTE: This no longer raises SizeofError bacuse that error means structure is variable size. If the context is missing entries then the error will reflect that, a missing key.")
        self.assertRaises(AttributeError, self.mf.sizeof)

    def test_sizeof(self):
        context = Container(length=4)
        self.assertEqual(self.mf.sizeof(context), 4)


class TestAligned(unittest.TestCase):

    def test_from_issue_76(self):
        def barLength(ctx):
            print("Context of field2 is", ctx)
            return ctx.field1
        test1 = Struct("test1",
            Aligned(
                Struct("test2",
                    ULInt8("field1"),
                    Field("field2", barLength)
                ),
                modulus=4,
            )
        )
        self.assertEqual(test1.parse(b"\x02\xab\xcd\x00"), Container(test2=Container(field1=2)(field2=b"\xab\xcd")))


class TestAnchor(unittest.TestCase):

    def test_in_struct(self):
        struct = Struct("struct",
            Byte("a"),
            Anchor("start_payload"),
            Byte("b"),
            Anchor("end_payload"),
        )
        self.assertEqual(struct.parse(b"\x01\x02"), Container(a=1)(start_payload=1)(b=2)(end_payload=2))
        self.assertEqual(struct.build(Container(a=1,b=2,start_payload=1,end_payload=2)), b"\x01\x02")
        self.assertEqual(struct.build(Container(a=1,b=2)), b"\x01\x02")

    def test_from_issue_60(self):
        Header = Struct("header",
            UBInt8("type"),
            Switch("size", lambda ctx: ctx.type,
            {
                0: UBInt8("size"),
                1: UBInt16("size"),
                2: UBInt32("size")
            }),
            Anchor("length"),
        )
        self.assertEqual(Header.parse(b"\x00\x05"), Container(type=0)(size=5)(length=2))
        self.assertEqual(Header.parse(b"\x01\x00\x05"), Container(type=1)(size=5)(length=3))
        self.assertEqual(Header.parse(b"\x02\x00\x00\x00\x05"), Container(type=2)(size=5)(length=5))

        self.assertEqual(Header.build(dict(type=0, size=5)), b"\x00\x05")
        self.assertEqual(Header.build(dict(type=1, size=5)), b"\x01\x00\x05")
        self.assertEqual(Header.build(dict(type=2, size=5)), b"\x02\x00\x00\x00\x05")

        HeaderData = Struct("header",
            Embed(Header),
            Bytes("data", lambda ctx: ctx.size),
        )
        self.assertEqual(HeaderData.build(dict(type=0, size=5, data=b"12345")), b"\x00\x0512345")
        self.assertEqual(HeaderData.build(dict(type=1, size=5, data=b"12345")), b"\x01\x00\x0512345")
        self.assertEqual(HeaderData.build(dict(type=2, size=5, data=b"12345")), b"\x02\x00\x00\x00\x0512345")


    def test_from_issue_71(self):
        class ValidatePayloadLength(Validator):
            def _validate(self, obj, ctx):
                return ctx.payload_end - ctx.payload_start == ctx.payload_len == len(ctx.raw_payload)
        class ChecksumValidator(Validator):
            def _validate(self, obj, ctx):
                return sha512(ctx.raw_payload).digest() == obj

        Outer = Struct("less_contrived_example",
            UBInt16('struct_type'),
            UBInt16('payload_len'),

            Anchor('payload_start'),
            Peek(String('raw_payload', length=lambda ctx: ctx.payload_len)),
            PascalString("name"),
            PascalString("occupation"),
            Anchor('payload_end'),

            UBInt16('serial'),

            ChecksumValidator(Bytes('checksum', 64)),
            ValidatePayloadLength(Pass),
            Terminator,
        )
        Inner = Struct('temp', 
            PascalString('name'), 
            PascalString('occupation'),
        )

        payload = Inner.build(Container(name=b"unknown", occupation=b"worker"))
        payload_len = len(payload)
        checksum = sha512(payload).digest()
        Outer.build(Container(name=b"unknown", occupation=b"worker", raw_payload=payload, payload_len=payload_len, checksum=checksum, serial=12345, struct_type=9001))


class TestChecksum(unittest.TestCase):

    def test(self):
        def sha512(b):
            return hashlib.sha512(b).digest()
        struct = Struct("struct",
            Byte("a"),
            AnchorRange("range"),
            Byte("b"),
            AnchorRange("range"),
            Checksum(Bytes("checksum",64), sha512, "range"),
            allow_overwrite=True,
        )
        c = b"\xfa\xb8H\xc9\xb6W\xa8S\xee7\xc0\x9c\xbf\xdd\x14\x9d\x0b8\x07\xb1\x91\xdd\xe9\xb6#\xcc\xd9R\x81\xdd\x18p[H\xc8\x9b\x15\x03\x908E\xbb\xa5u9E5\x1f\xe6\xb4T\x85'`\xf75)\xcf\x01\xca\x8fi\xdc\xca"
        self.assertEqual(sha512(b"\x02"), c)
        self.assertEqual(struct.parse(b"\x01\x02"+c), Container(a=1)(range=Container(offset1=1)(offset2=2)(length=1))(b=2)(checksum=c))
        self.assertEqual(struct.build(dict(a=1,b=2)), b"\x01\x02"+c)


class TestEmbedOptional(unittest.TestCase):

    def test_from_issue_28(self):
        def vstring(name, embed=True, optional=True):
            lfield = "_%s_length" % name.lower()
            s = Struct(name,
                ULInt8(lfield),
                String(name, lambda ctx: getattr(ctx, lfield)))
            if optional:
                s = Optional(s)
            if embed:
                s = Embed(s)
            return s

        def build_struct(embed_g=True, embed_h=True):
            s = Struct(
                "mystruct",
                ULInt32("a"),
                ULInt8("b"),
                ULInt8("c"),
                BitStruct(
                    "d",
                    BitField("d_bit7", 1),
                    BitField("d_bit6", 1),
                    BitField("d_bit5", 1),
                    BitField("d_bit4", 1),
                    BitField("d_bit3", 1),
                    BitField("d_bit2", 1),
                    BitField("d_bit1", 1),
                    BitField("d_bit0", 1)),
                BitStruct(
                    "e",
                    BitField("e_bit7", 1),
                    BitField("e_bit6", 1),
                    BitField("e_bit5", 1),
                    BitField("e_bit4", 1),
                    BitField("e_bit3", 1),
                    BitField("e_bit2", 1),
                    BitField("e_bit1", 1),
                    BitField("e_bit0", 1)),
                BFloat32("f"),
                vstring("g", embed=embed_g),
                vstring("h", embed=embed_h),
                BitStruct(
                    "i",
                    BitField("i_bit7", 1),
                    BitField("i_bit6", 1),
                    BitField("i_bit5", 1),
                    BitField("i_bit4", 1),
                    BitField("i_bit3", 1),
                    BitField("i_bit2", 1),
                    BitField("i_bit1", 1),
                    BitField("i_bit0", 1)),
                SBInt8("j"),
                SBInt8("k"),
                SBInt8("l"),
                LFloat32("m"),
                LFloat32("n"),
                vstring("o"),
                vstring("p"),
                vstring("q"),
                vstring("r"))
            return s

        data = b'\xc3\xc0{\x00\x01\x00\x00\x00HOqA\x12some silly text...\x00\x0e\x00\x00\x00q=jAq=zA\x02dB\x02%f\x02%f\x02%f'
        print("\n\nNo embedding for neither g and h, i is a container --> OK")
        print(build_struct(embed_g=False, embed_h=False).parse(data))
        print("Embed both g and h, i is not a container --> FAIL")
        print(build_struct(embed_g=True, embed_h=True).parse(data))
        print("\n\nEmbed g but not h --> EXCEPTION")
        print(build_struct(embed_g=True, embed_h=False).parse(data))
        # When setting optional to False in vstring method, all three tests above work fine.


class TestTunnelZlib(unittest.TestCase):

    def test_from_issue_38(self):
        s = TunnelAdapter(
            PascalString("data", encoding = "zlib"),
            GreedyRange(UBInt16("elements")),
        )
        obj = [1 for i in range(100)]
        output = b"\rx\x9cc`d\x18\x16\x10\x00'\xd8\x00e"
        self.assertEqual(s.parse(output), obj)
        self.assertEqual(s.build(obj), output)
