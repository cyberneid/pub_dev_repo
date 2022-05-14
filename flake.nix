{
  description = "A very simple selfhostable pub repository for Dart and Flutter with support for publishing.";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  outputs = {
    self,
    nixpkgs
  }: let
    supportedSystems = [ "x86_64-linux" ];
    forAllSystems = nixpkgs.lib.attrsets.genAttrs supportedSystems;
  in {
    packages = forAllSystems (system: let
      pkgs = import nixpkgs { inherit system; };

      pub_repo = pkgs.callPackage ./pkgs/pub_repo.nix {};
    in {
      inherit pub_repo;
      default = pub_repo;
    });

    nixosModule = { config, lib, pkgs, ... }: let
      cfg = config.polynom.services.pub_repo;
      pub_repo = self.packages.${pkgs.system}.pub_repo;
    in {
      options.polynom.services.pub_repo = {
        enable = lib.mkEnableOption "Enable pub_repo.";

        uid = lib.mkOption {
          example = 9998;
          description = "The UID of the user running pub_repo";
          default = 9998;
        };
        gid = lib.mkOption {
          example = 9998;
          description = "The GID of the user running pub_repo";
          default = 9998;
        };
        port = lib.mkOption {
          example = 9998;
          description = "The HTTP port on which pub_repo will be accessible";
          default = 9998;
        };
        datadir = lib.mkOption {
          example = "/var/lib/pubrepo";
          description = "The place all data is stored";
          default = "/var/lib/pubrepo";
        };
        configFile = lib.mkOption {
          example = "/etc/pub_repo/config.yaml";
          description = "Path to the configuration file";
        };
      };

      config = lib.mkIf cfg.enable {
        users.users.pubrepo = {
          name = "pubrepo";
          group = "pubrepo";
          uid = cfg.uid;
          home = cfg.datadir;
          isSystemUser = true;
        };
        users.groups.pubrepo = {
          gid = cfg.gid;
        };
        
        systemd.services.pubrepo = let
          pythonEnv = pkgs.python3.withPackages (ps: with ps; [
            daphne pub_repo
          ]);
        in {
          description = "Simple pub repository";
          after = [ "network-online.target" ];
          wants = [ "network-online.target" ];
          wantedBy = [ "multi-user.target" ];
          restartTriggers = [ cfg.configFile ];
          environment = {
            PYTHONPATH = "${pythonEnv}/${pkgs.python3.sitePackages}";
            PUB_REPO_CONFIG = cfg.configFile;
          };
          script = ''
            ${pythonEnv}/bin/daphne \
              -b 0.0.0.0 \
              -p ${toString cfg.port} \
              pub_repo.repo_asgi:app
          '';
          
          serviceConfig = {
            User = "pubrepo";
            Group = "pubrepo";
            Type = "simple";
            
            MemoryDenyWriteExecute = true;
            PrivateDevices = true;
            PrivateMounts = true;
            PrivateTmp = true;
            ProtectHome = true;
            ProtectHostname = true;
            RestrictSUIDSGID = true;
            DevicePolicy = "closed";
            NoNewPrivileges = true;
            PrivateUsers = true;
            ProtectControlGroups = true;
            ProtectKernelModules = true;
            ProtectKernelTunables = true;
            ProtectProc = "noaccess";
            ProcSubset = "pid";
            ProtectKernelLogs = true;
            RestrictAddressFamilies = "AF_INET";
            CapabilityBoundingSet = "~CAP_SETPCAP CAP_SYS_ADMIN CAP_SYS_PTRACE CAP_NET_ADMIN CAP_SYS_TIME CAP_KILL CAP_SYS_CHROOT CAP_SYS_TTY_CONFIG CAP_WAKE_ALARM CAP_NET_RAW CAP_NET_BROADCAST CAP_NET_BIND_SERVICE CAP_SYS_NICE CAP_SYS_RESOURCE CAP_MAC_ADMIN CAP_MAC_OVERRIDE CAP_SYS_BOOT CAP_AUDIT_CONTROL CAP_AUDIT_READ CAP_AUDIT_WRITE CAP_SYS_PACCT CAP_LEASE CAP_BLOCK_SUSPEND CAP_LINUX_IMMUTABLE CAP_FOWNER CAP_IPC_OWNER CAP_DAC_OVERRIDE CAP_DAC_READ_SEARCH CAP_SETUID CAP_SETGID CAP_SETPCAP";
            SystemCallArchitectures = "native";
            LockPersonality = true;
            ProtectClock = true;
            RestrictNamespaces = true;
            RestrictRealtime = true;
            SystemCallFilter = "~@clock @debug @module @mount @obsolete @reboot @setuid @swap @resources @raw-io @cpu-emulation";
            ReadWritePaths = cfg.datadir;
            ReadOnlyPaths = [ cfg.configFile ];
            ProtectSystem = "full";
          };
        };
      };
    };
  };
}
