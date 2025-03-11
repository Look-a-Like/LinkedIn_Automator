import { Link } from 'react-router-dom';
import {
  Home,
  LineChart,
  Landmark,
  Settings,
  Users
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function NavBar() {
  return (
    <div className="flex min-h-screen w-full bg-muted/40">
      <aside className="fixed top-10 bottom-10 left-8 z-10 w-20 flex flex-col bg-red-400 rounded-3xl">
        <div className="flex flex-col items-center mb-auto mt-10">
          <Link
            to="#"
            className="group flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary text-lg font-semibold text-primary-foreground mb-8"
          >
            <span className="text-white">Logo</span>
          </Link>

          <nav className="flex flex-col items-center gap-6">
            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    to="/MainPage"
                    className="flex h-12 w-12 items-center justify-center rounded-full text-white transition-colors hover:bg-gray-200 hover:text-black"
                  >
                    <Home className="h-6 w-6" />
                    <span className="sr-only">Home</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">Home</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    to="/Applications"
                    className="flex h-12 w-12 items-center justify-center rounded-full text-white transition-colors hover:bg-gray-200 hover:text-black"
                  >
                    <LineChart className="h-6 w-6" />
                    <span className="sr-only">Applications Page</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">Applications Page</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    to="/Companies"
                    className="flex h-12 w-12 items-center justify-center rounded-full text-white transition-colors hover:bg-gray-200 hover:text-black"
                  >
                    <Landmark className="h-6 w-6" />
                    <span className="sr-only">Companies Listing</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">Companies Listing</TooltipContent>
              </Tooltip>
            </TooltipProvider>

            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link
                    to="/Jobs"
                    className="flex h-12 w-12 items-center justify-center rounded-full bg-white text-black transition-colors hover:bg-gray-200 hover:text-black"
                  >
                    <Users className="h-6 w-6" />
                    <span className="sr-only">Jobs Listing Page</span>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">Jobs Listing Page</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </nav>
        </div>
        
        <div className="flex flex-col items-center mt-auto mb-10">
          <TooltipProvider delayDuration={150}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link
                  to="/Settings"
                  className="flex h-12 w-12 items-center justify-center rounded-full text-white transition-colors hover:bg-gray-200 hover:text-black"
                >
                  <Settings className="h-6 w-6" />
                  <span className="sr-only">Settings</span>
                </Link>
              </TooltipTrigger>
              <TooltipContent side="right">Settings</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </aside>
    </div>
  );
}

export default NavBar;
