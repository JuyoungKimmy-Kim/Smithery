import Image from "next/image";

interface ArticleCardProps {
    img: string;
    title: string;
    desc: string;
  }
  
  export function ArticleCard({ img, title, desc }: ArticleCardProps) {
    return (
      <div className="relative grid min-h-[30rem] items-end overflow-hidden rounded-xl bg-transparent">
        <Image
          width={768}
          height={768}
          src={img}
          alt="bg"
          className="absolute inset-0 h-full w-full object-cover object-center"
        />
        <div className="absolute inset-0 bg-black/60" />
        <div className="relative flex flex-col justify-end p-6">
          <h2 className="text-2xl font-bold text-white">
            {title}
          </h2>
          <p className="text-white my-2 font-normal">
            {desc}
          </p>
        </div>
      </div>
    );
  }

  export default ArticleCard;