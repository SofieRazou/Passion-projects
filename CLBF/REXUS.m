% % System parameters
% J1  = 0.02;
% J2  = 0.03;
% Iw1 = 0.001;
% Iw2 = 0.001;
% 
% % System matrices
% A = [0 0 1 0 0 0;
%      0 0 0 1 0 0;
%      0 0 0 0 0 0;
%      0 0 0 0 0 0;
%      0 0 0 0 0 0;
%      0 0 0 0 0 0];
% 
% B = [0 0;
%      0 0;
%     -1/J1 0;
%      0 -1/J2;
%      1/Iw1 0;
%      0 1/Iw2];
% 
A = [10 2; 5 13];
B = [0 ; 0.1];
C = eye(2);
D = [0;0];
def = legacy_code('initialize');
def.SFunctionName = 'sfun_qp_wrapper';
def.OutputFcnSpec = 'double y1 = solve_qp_wrapper(double u1, double u2)';
def.HeaderFiles   = {'solver_wrapper.hpp'};
def.SourceFiles   = {'solver_wrapper.cpp','qp_solver.cpp'};
def.IncPaths      = { ...
    '/Users/sofia/Desktop/projects_4_exercise/simulink_projects', ...
    '/opt/homebrew/Cellar/eigen/5.0.1/include/eigen3' ...
};
def.SrcPaths      = {'/Users/sofia/Desktop/projects_4_exercise/simulink_projects'};
def.Options.language = 'C++';

legacy_code('sfcn_cmex_generate', def);

% def = legacy_code('initialize');
% def.SFunctionName = 'sfun_qp_wrapper';
% def.OutputFcnSpec = 'double y1 = solve_qp_wrapper(double u1, double u2)';
% def.HeaderFiles   = {'wrapper.hpp'};
% def.SourceFiles   = {'wrapper.cpp','control.cpp'};
% def.IncPaths      = { ...
%     '/Users/sofia/Desktop/projects_4_exercise/simulink_projects', ...
%     '/opt/homebrew/Cellar/eigen/5.0.1/include/eigen3' ...
% };
% def.SrcPaths      = {'/Users/sofia/Desktop/projects_4_exercise/simulink_projects'};
% def.Options.language = 'C++';
% 
% legacy_code('sfcn_cmex_generate', def);