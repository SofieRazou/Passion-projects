def = legacy_code('initialize');
def.SFunctionName = 'sfun_PHwrapper';
def.OutputFcnSpec = 'double y1 = PH_wrapper(double u1, double u2)';
def.HeaderFiles   = {'PHwrapper.hpp'};
def.SourceFiles   = {'PHwrapper.cpp','PHham.cpp'};
def.IncPaths      = { ...
    '/Users/sofia/Desktop', ...
    '/opt/homebrew/Cellar/eigen/5.0.1/include/eigen3' ...
};
def.SrcPaths      = {'/Users/sofia/Desktop'};
def.Options.language = 'C++';

legacy_code('sfcn_cmex_generate', def);
legacy_code('compile', def);
legacy_code('slblock_generate', def);
