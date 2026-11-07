import logo from "../assets/artha_logo_light.png";
import mark from "../assets/artha_mark.png";

export function ArthaBrand({ variant }: { variant: "login" | "sidebar" }) {
  if (variant === "login") {
    return (
      <div className="brand">
        <img className="brand-logo" src={logo} alt="Artha" width={1080} height={300} />
      </div>
    );
  }

  return (
    <div className="brand">
      <img className="brand-mark" src={mark} alt="" width={1024} height={1024} />
      <span>
        Artha<small>IMPORT WORKSPACE</small>
      </span>
    </div>
  );
}
