define metadata
   help metadata
end

document metadata
Renode simulator commands:
   rstart   - renode start
   rquit    - renode quit
Metadata related commnads:
   pvm      - print violation message
   lre      - print last rule evaluation
   env-m    - get the env metadata
   reg-m n  - get register n metadata
   areg-m   - get all register metadata
   csr-m a  - get csr metadata at addr a
   mem-m a  - get mem metadata at addr a
Watchpoints halt simulation when metadata changes
   env-mw   - set watch on the env metadata
   reg-mw n - set watch on register n metadata
   csr-mw a - set watch on csr metadata at addr a
   mem-mw a - set watch on mem metadata at addr a
end

define pvm
   monitor sysbus.ap_core PolicyViolationMsg
end

document pvm
   Command to print last policy violation info
   Only captures the last violation info.
end

define lre
   monitor sysbus.ap_core RuleEvalLog
end

document lre
   Command to print last rule evaluation info
end

define rstart
   monitor start
end

define rquit
   monitor quit
end

define env-m
   monitor sysbus.ap_core EnvMetadata
end

document env-m
   get environment metadata
end

define reg-m
   monitor sysbus.ap_core RegMetadata $arg0
end

document reg-m
   get register metadata
end

define areg-m
   monitor sysbus.ap_core AllRegMetadata
end

document areg-m
   get all register metadata
end

define csr-m
   monitor sysbus.ap_core CsrMetadata $arg0
end
document csr-m
   get csr metadata at addr
end

define mem-m
   monitor sysbus.ap_core MemMetadata $arg0
end
document mem-m
   get mem metadata at addr
end

define env-mw
   monitor sysbus.ap_core EnvMetadataWatch true
end
document env-mw
   set watch on the env metadata
end

define reg-mw
   monitor sysbus.ap_core RegMetadataWatch $arg0
end
document reg-mw
   set watch on register metadata
end

define csr-mw
   monitor sysbus.ap_core CsrMetadataWatch $arg0
end
document csr-mw
   set watch on csr metadata at addr
end

define mem-mw
   monitor sysbus.ap_core MemMetadataWatch $arg0
end
document mem-mw
   set watch on mem metadata at addr
end



define hook-stop
   pvm
end

set confirm off
