BUILDDIR = build

OPTIONS  = -d build/html -t

OPTIONS += $(foreach theme,$(THEMES),-T $(theme))
OPTIONS += $(HTML_OPTS)

.PHONY: usage clean hobbit
usage:
	@echo "Targets:"
	@echo "  usage      show this help"
	@echo "  hobbit     build the The Hobbit disassembly"
	@echo ""
	@echo "Variables:"
	@echo "  THEMES     CSS theme(s) to use"
	@echo "  HTML_OPTS  options passed to skool2html.py"

.PHONY: clean
clean:
	-rm -rf $(BUILDDIR)/*

.PHONY: hobbit
hobbit:
	if [ ! -f HobbitThe.z80 ]; then tap2sna.py @hobbit.t2s; fi
	sna2skool.py -H -c sources/hobbit.ctl HobbitThe.z80 > sources/hobbit.skool
	skool2html.py $(OPTIONS) -D -c Config/GameDir=hobbit/dec -c Config/InitModule=sources:bases sources/hobbit.skool sources/hobbit.ref
	skool2html.py $(OPTIONS) -H -c Config/GameDir=hobbit/hex -c Config/InitModule=sources:bases sources/hobbit.skool sources/hobbit.ref

all : hobbit
.PHONY : all
