import debug
import design
from tech import drc
from math import log
from vector import vector
from globals import OPTS
from pinv import pinv

class dff_inv(design.design):
    """
    This is a simple DFF with an inverted output. Some DFFs
    do not have Qbar, so this will create it.
    """

    def __init__(self, inv_size=1, name=""):

        if name=="":
            name = "dff_inv_{0}".format(inv_size)
        design.design.__init__(self, name)
        debug.info(1, "Creating {}".format(self.name))

        c = reload(__import__(OPTS.dff))
        self.mod_dff = getattr(c, OPTS.dff)
        self.dff = self.mod_dff("dff")
        self.add_mod(self.dff)

        self.inv1 = pinv(size=inv_size,height=self.dff.height)
        self.add_mod(self.inv1)

        self.width = self.dff.width + self.inv1.width
        self.height = self.dff.height

        self.create_layout()

    def create_layout(self):
        self.add_pins()
        self.add_insts()
        self.add_wires()
        self.add_layout_pins()
        self.DRC_LVS()
        
    def add_pins(self):
        self.add_pin("D")
        self.add_pin("Q")
        self.add_pin("Qb")
        self.add_pin("clk")
        self.add_pin("vdd")
        self.add_pin("gnd")

    def add_insts(self):
        # Add the DFF
        self.dff_inst=self.add_inst(name="dff_inv_dff",
                                    mod=self.dff,
                                    offset=vector(0,0))
        self.connect_inst(["D", "Q", "clk", "vdd", "gnd"])

        # Add INV1 to the right
        self.inv1_inst=self.add_inst(name="dff_inv_inv1",
                                     mod=self.inv1,
                                     offset=vector(self.dff_inst.rx(),0))
        self.connect_inst(["Q", "Qb",  "vdd", "gnd"])
        
        
    def add_wires(self):
        # Route dff q to inv1 a
        q_pin = self.dff_inst.get_pin("Q")
        a1_pin = self.inv1_inst.get_pin("A")
        mid_point = vector(a1_pin.cx(), q_pin.cy())
        self.add_wire(("metal3","via2","metal2"),
                      [q_pin.center(), mid_point, a1_pin.center()])
        self.add_via_center(("metal2","via2","metal3"),
                            q_pin.center())
        self.add_via_center(("metal1","via1","metal2"),
                            a1_pin.center())

        
    def add_layout_pins(self):

        # Continous vdd rail along with label.
        vdd_pin=self.dff_inst.get_pin("vdd")
        self.add_layout_pin(text="vdd",
                            layer="metal1",
                            offset=vdd_pin.ll(),
                            width=self.width,
                            height=vdd_pin.height())

        # Continous gnd rail along with label.
        gnd_pin=self.dff_inst.get_pin("gnd")
        self.add_layout_pin(text="gnd",
                            layer="metal1",
                            offset=gnd_pin.ll(),
                            width=self.width,
                            height=vdd_pin.height())
            
        clk_pin = self.dff_inst.get_pin("clk")
        self.add_layout_pin(text="clk",
                            layer=clk_pin.layer,
                            offset=clk_pin.ll(),
                            width=clk_pin.width(),
                            height=clk_pin.height())

        din_pin = self.dff_inst.get_pin("D")
        self.add_layout_pin(text="D",
                            layer=din_pin.layer,
                            offset=din_pin.ll(),
                            width=din_pin.width(),
                            height=din_pin.height())

        dout_pin = self.dff_inst.get_pin("Q")
        self.add_layout_pin_center_rect(text="Q",
                                        layer=dout_pin.layer,
                                        offset=dout_pin.center())

        dout_pin = self.inv1_inst.get_pin("Z")
        self.add_layout_pin_center_rect(text="Qb",
                                        layer="metal2",
                                        offset=dout_pin.center())
        self.add_via_center(layers=("metal1","via1","metal2"),
                            offset=dout_pin.center())
        
        

    def analytical_delay(self, slew, load=0.0):
        """ Calculate the analytical delay of DFF-> INV -> INV """
        dff_delay=self.dff.analytical_delay(slew=slew, load=self.inv1.input_load())
        inv1_delay = self.inv1.analytical_delay(slew=dff_delay.slew, load=load) 
        return dff_delay + inv1_delay 
            
