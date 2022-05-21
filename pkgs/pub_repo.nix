{
  lib, stdenv, python3
, fetchgit
}:

python3.pkgs.buildPythonPackage rec {
  pname = "pub_repo";
  version = "0.1.3";

  src = ../.;
  
  propagatedBuildInputs = with python3.pkgs; [
    pyyaml
    falcon
    jinja2
  ];
  doCheck = false;
  
  meta = with lib; {
    homepage = "https://codeberg.org/PapaTutuWawa/pub_repo";
    description = "A very simple selfhostable pub repository for Dart and Flutter with support for publishing.";
    license = licenses.gpl3;
  };
}
